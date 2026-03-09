// ============================================================================
// Go 並行処理パターン - FAANG面接レベル完全ガイド
// ============================================================================
// 実行: go run go_concurrency_patterns.go
//
// このファイルでは Go の並行処理パターンを実装しながら学ぶ。
// 標準ライブラリのみ使用。各パターンは独立したデモとして実行される。
// ============================================================================

package main

import (
	"context"
	"errors"
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
)

// ============================================================================
// 1. Goroutine & Channel 基礎 - Fan-out / Fan-in パターン
// ============================================================================
// 考えてほしい疑問:
//   - Fan-outで goroutine数を無制限にするとどうなる？
//   - Fan-inで1つのgoroutineが遅い場合、全体のスループットはどうなる？
//   - バッファありチャネルとなしチャネル、どちらを使うべき？

// generator は値を生成してチャネルに送る（Producer）
func generator(nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out) // 重要: 送信完了後にcloseする
		for _, n := range nums {
			out <- n
		}
	}()
	return out
}

// square はチャネルから値を受け取り、二乗してチャネルに送る（Fan-out用ワーカー）
func square(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			out <- n * n
		}
	}()
	return out
}

// fanIn は複数のチャネルを1つにまとめる（Fan-in）
// WaitGroupを使って全入力チャネルが閉じたら出力チャネルも閉じる
func fanIn(channels ...<-chan int) <-chan int {
	var wg sync.WaitGroup
	merged := make(chan int)

	// 各入力チャネルからmergedに転送するgoroutineを起動
	for _, ch := range channels {
		wg.Add(1)
		go func(c <-chan int) {
			defer wg.Done()
			for val := range c {
				merged <- val
			}
		}(ch)
	}

	// 全チャネルが完了したらmergedを閉じる
	go func() {
		wg.Wait()
		close(merged)
	}()

	return merged
}

func demoFanOutFanIn() {
	fmt.Println("=== 1. Fan-out / Fan-in パターン ===")

	// 入力チャネルを生成
	input := generator(1, 2, 3, 4, 5, 6, 7, 8)

	// Fan-out: 同じ入力チャネルから3つのワーカーが読み取る
	w1 := square(input)
	w2 := square(input) // 同じinputを共有 → 自動的に仕事が分散
	w3 := square(input)

	// Fan-in: 3つのワーカーの出力を1つにまとめる
	results := fanIn(w1, w2, w3)

	var sum int
	for r := range results {
		fmt.Printf("  二乗結果: %d\n", r)
		sum += r
	}
	fmt.Printf("  合計: %d\n\n", sum)
}

// ============================================================================
// 2. select 文 - Timeout, Cancellation, Multiplexing
// ============================================================================
// 考えてほしい疑問:
//   - selectで複数のcaseが同時にreadyになったら、どれが実行される？
//   - time.After はgoroutineリークの原因になりうる。なぜ？

func demoSelect() {
	fmt.Println("=== 2. select 文 ===")

	// 2つのチャネルからの多重化
	ch1 := make(chan string)
	ch2 := make(chan string)

	go func() {
		time.Sleep(50 * time.Millisecond)
		ch1 <- "チャネル1からのデータ"
	}()
	go func() {
		time.Sleep(30 * time.Millisecond)
		ch2 <- "チャネル2からのデータ"
	}()

	// Multiplexing: 先に来た方を受信
	for i := 0; i < 2; i++ {
		select {
		case msg := <-ch1:
			fmt.Printf("  受信(ch1): %s\n", msg)
		case msg := <-ch2:
			fmt.Printf("  受信(ch2): %s\n", msg)
		}
	}

	// Timeout パターン
	slowCh := make(chan string)
	go func() {
		time.Sleep(200 * time.Millisecond)
		slowCh <- "遅いレスポンス"
	}()

	select {
	case msg := <-slowCh:
		fmt.Printf("  受信: %s\n", msg)
	case <-time.After(100 * time.Millisecond):
		fmt.Println("  タイムアウト! 100ms以内にレスポンスなし")
	}

	// Non-blocking send/receive（defaultケース）
	nonBlockCh := make(chan int, 1)
	select {
	case nonBlockCh <- 42:
		fmt.Println("  非ブロッキング送信: 成功")
	default:
		fmt.Println("  非ブロッキング送信: チャネルがいっぱい")
	}
	fmt.Println()
}

// ============================================================================
// 3. context.Context - キャンセル伝播パイプライン
// ============================================================================
// 考えてほしい疑問:
//   - context.Backgroundと context.TODO の違いは？
//   - WithValue は便利だが濫用すると何が問題になる？
//   - なぜHTTPハンドラの第一引数にContextを渡す設計なのか？

// fetchData はcontextのキャンセルを監視しながらデータを生成するパイプラインステージ
func fetchData(ctx context.Context, id int) <-chan string {
	out := make(chan string)
	go func() {
		defer close(out)
		for i := 0; ; i++ {
			select {
			case <-ctx.Done():
				fmt.Printf("  [fetchData-%d] キャンセル検知: %v\n", id, ctx.Err())
				return
			case out <- fmt.Sprintf("data-%d-%d", id, i):
				time.Sleep(20 * time.Millisecond) // データ生成をシミュレート
			}
		}
	}()
	return out
}

func demoContext() {
	fmt.Println("=== 3. context.Context ===")

	// WithCancel: 明示的キャンセル
	ctx, cancel := context.WithCancel(context.Background())
	dataCh := fetchData(ctx, 1)

	// 3件だけ受信してキャンセル
	for i := 0; i < 3; i++ {
		fmt.Printf("  受信: %s\n", <-dataCh)
	}
	cancel() // パイプライン全体をキャンセル
	time.Sleep(50 * time.Millisecond)

	// WithTimeout: 自動タイムアウト
	ctx2, cancel2 := context.WithTimeout(context.Background(), 80*time.Millisecond)
	defer cancel2() // 重要: タイムアウト前に完了しても必ずcancelを呼ぶ（リソースリーク防止）

	dataCh2 := fetchData(ctx2, 2)
	count := 0
	for range dataCh2 {
		count++
	}
	fmt.Printf("  WithTimeout: タイムアウトまでに %d 件受信\n", count)

	// WithValue: リクエストスコープの値伝播
	type contextKey string
	const requestIDKey contextKey = "requestID"

	ctx3 := context.WithValue(context.Background(), requestIDKey, "req-abc-123")
	if reqID, ok := ctx3.Value(requestIDKey).(string); ok {
		fmt.Printf("  WithValue: requestID = %s\n", reqID)
	}
	fmt.Println()
}

// ============================================================================
// 4. sync パッケージ - Mutex, RWMutex, WaitGroup, Once, Pool, Map
// ============================================================================
// 考えてほしい疑問:
//   - MutexとRWMutexの使い分けの基準は？
//   - sync.Poolに入れたオブジェクトはいつGCされる？
//   - sync.Mapは普通のmap+Mutexより常に速い？

// SafeCounter はMutexで保護されたカウンター
type SafeCounter struct {
	mu sync.RWMutex
	v  map[string]int
}

func (c *SafeCounter) Inc(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.v[key]++
}

func (c *SafeCounter) Get(key string) int {
	c.mu.RLock() // 読み取り専用ロック（複数goroutineが同時に読める）
	defer c.mu.RUnlock()
	return c.v[key]
}

func demoSync() {
	fmt.Println("=== 4. sync パッケージ ===")

	// --- Mutex / RWMutex ---
	counter := SafeCounter{v: make(map[string]int)}
	var wg sync.WaitGroup

	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			counter.Inc("key")
		}()
	}
	wg.Wait()
	fmt.Printf("  Mutex: counter[\"key\"] = %d (期待値: 100)\n", counter.Get("key"))

	// --- sync.Once ---
	var once sync.Once
	initMsg := ""
	for i := 0; i < 5; i++ {
		once.Do(func() {
			initMsg = "初期化完了" // 何回呼んでも1回だけ実行される
		})
	}
	fmt.Printf("  Once: %s\n", initMsg)

	// --- sync.Pool ---
	// 一時オブジェクトの再利用でGC負荷を軽減
	bufferPool := sync.Pool{
		New: func() interface{} {
			buf := make([]byte, 0, 1024)
			return &buf
		},
	}

	// Poolから取得して使い、戻す
	bufPtr := bufferPool.Get().(*[]byte)
	*bufPtr = append(*bufPtr, []byte("hello pool")...)
	fmt.Printf("  Pool: バッファ内容 = %s\n", string(*bufPtr))
	*bufPtr = (*bufPtr)[:0] // リセットしてから戻す
	bufferPool.Put(bufPtr)

	// --- sync.Map ---
	// 読み取りが多く、キーが安定している場合に有効
	var sm sync.Map
	sm.Store("golang", "素晴らしい")
	sm.Store("concurrency", "強力")

	sm.Range(func(key, value interface{}) bool {
		fmt.Printf("  sync.Map: %s = %s\n", key, value)
		return true // falseを返すと反復停止
	})
	fmt.Println()
}

// ============================================================================
// 5. errgroup パターン - 並行処理のエラー収集（標準ライブラリのみで実装）
// ============================================================================
// 考えてほしい疑問:
//   - errgroupで1つのgoroutineがエラーを返したら、他はどうなるべき？
//   - 全エラーを収集したい場合とfail-fastの場合、設計はどう変わる？

// ErrGroup は golang.org/x/sync/errgroup を標準ライブラリだけで再現
type ErrGroup struct {
	wg      sync.WaitGroup
	errOnce sync.Once
	err     error
	ctx     context.Context
	cancel  context.CancelFunc
}

// NewErrGroup は新しいErrGroupを生成する
func NewErrGroup(ctx context.Context) (*ErrGroup, context.Context) {
	ctx, cancel := context.WithCancel(ctx)
	return &ErrGroup{ctx: ctx, cancel: cancel}, ctx
}

// Go はgoroutineを起動し、エラーがあれば記録してcontextをキャンセルする
func (g *ErrGroup) Go(f func() error) {
	g.wg.Add(1)
	go func() {
		defer g.wg.Done()
		if err := f(); err != nil {
			g.errOnce.Do(func() {
				g.err = err
				g.cancel() // 最初のエラーで他のgoroutineにもキャンセルを伝播
			})
		}
	}()
}

// Wait は全goroutineの完了を待ち、最初のエラーを返す
func (g *ErrGroup) Wait() error {
	g.wg.Wait()
	g.cancel() // リソースリーク防止
	return g.err
}

func demoErrGroup() {
	fmt.Println("=== 5. errgroup パターン ===")

	// 複数のAPIを並行に呼ぶシミュレーション
	eg, ctx := NewErrGroup(context.Background())
	results := make([]string, 3)

	apis := []struct {
		name  string
		delay time.Duration
		fail  bool
	}{
		{"UserAPI", 30 * time.Millisecond, false},
		{"OrderAPI", 50 * time.Millisecond, true}, // これが失敗する
		{"ProductAPI", 40 * time.Millisecond, false},
	}

	for i, api := range apis {
		i, api := i, api // ループ変数キャプチャ
		eg.Go(func() error {
			select {
			case <-ctx.Done():
				fmt.Printf("  [%s] キャンセルされた\n", api.name)
				return ctx.Err()
			case <-time.After(api.delay):
				if api.fail {
					return fmt.Errorf("%s: 503 Service Unavailable", api.name)
				}
				results[i] = fmt.Sprintf("%s: OK", api.name)
				fmt.Printf("  [%s] 成功\n", api.name)
				return nil
			}
		})
	}

	if err := eg.Wait(); err != nil {
		fmt.Printf("  エラー発生: %v\n", err)
	}
	for _, r := range results {
		if r != "" {
			fmt.Printf("  結果: %s\n", r)
		}
	}
	fmt.Println()
}

// ============================================================================
// 6. Worker Pool パターン - 有界並行処理
// ============================================================================
// 考えてほしい疑問:
//   - ワーカー数はCPUコア数に合わせるべき？I/Oバウンドの場合は？
//   - ジョブキューのバッファサイズはどう決める？

// Job はワーカーが処理するタスクを表す
type Job struct {
	ID      int
	Payload string
}

// Result はジョブの処理結果を表す
type Result struct {
	JobID  int
	Output string
	Err    error
}

// workerPool はワーカーを管理し、ジョブを分配する
func workerPool(ctx context.Context, numWorkers int, jobs <-chan Job) <-chan Result {
	results := make(chan Result, numWorkers)
	var wg sync.WaitGroup

	// 固定数のワーカーgoroutineを起動
	for w := 0; w < numWorkers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for job := range jobs {
				select {
				case <-ctx.Done():
					results <- Result{JobID: job.ID, Err: ctx.Err()}
					return
				default:
					// 処理をシミュレート
					time.Sleep(time.Duration(10+rand.Intn(30)) * time.Millisecond)
					output := fmt.Sprintf("Worker-%d が Job-%d を処理: %s",
						workerID, job.ID, strings.ToUpper(job.Payload))
					results <- Result{JobID: job.ID, Output: output}
				}
			}
		}(w)
	}

	// 全ワーカー完了後に結果チャネルを閉じる
	go func() {
		wg.Wait()
		close(results)
	}()

	return results
}

func demoWorkerPool() {
	fmt.Println("=== 6. Worker Pool パターン ===")

	jobs := make(chan Job, 10)
	ctx := context.Background()

	// 3つのワーカーで8つのジョブを処理
	results := workerPool(ctx, 3, jobs)

	// ジョブを投入
	go func() {
		tasks := []string{"alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"}
		for i, t := range tasks {
			jobs <- Job{ID: i + 1, Payload: t}
		}
		close(jobs) // 全ジョブ投入完了
	}()

	// 結果を収集
	for r := range results {
		if r.Err != nil {
			fmt.Printf("  エラー: Job-%d: %v\n", r.JobID, r.Err)
		} else {
			fmt.Printf("  %s\n", r.Output)
		}
	}
	fmt.Println()
}

// ============================================================================
// 7. Pipeline パターン - ステージベース処理とグレースフルシャットダウン
// ============================================================================
// 考えてほしい疑問:
//   - パイプラインの各ステージのバッファサイズは同じにすべき？
//   - バックプレッシャーはどうやって実現する？

// ステージ1: 数値生成
func pipelineGenerate(ctx context.Context, nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for _, n := range nums {
			select {
			case <-ctx.Done():
				return
			case out <- n:
			}
		}
	}()
	return out
}

// ステージ2: フィルタ（偶数のみ通す）
func pipelineFilter(ctx context.Context, in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			if n%2 == 0 {
				select {
				case <-ctx.Done():
					return
				case out <- n:
				}
			}
		}
	}()
	return out
}

// ステージ3: 変換（3倍にする）
func pipelineTransform(ctx context.Context, in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			select {
			case <-ctx.Done():
				return
			case out <- n * 3:
			}
		}
	}()
	return out
}

func demoPipeline() {
	fmt.Println("=== 7. Pipeline パターン ===")

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// パイプライン構築: 生成 → フィルタ(偶数) → 変換(3倍)
	stage1 := pipelineGenerate(ctx, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
	stage2 := pipelineFilter(ctx, stage1)
	stage3 := pipelineTransform(ctx, stage2)

	fmt.Print("  偶数を3倍: ")
	for result := range stage3 {
		fmt.Printf("%d ", result) // 6 12 18 24 30
	}
	fmt.Println()

	// キャンセルによるグレースフルシャットダウンのデモ
	ctx2, cancel2 := context.WithCancel(context.Background())
	infinite := pipelineGenerate(ctx2, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
	filtered := pipelineFilter(ctx2, infinite)
	transformed := pipelineTransform(ctx2, filtered)

	count := 0
	for result := range transformed {
		fmt.Printf("  途中キャンセルデモ: %d\n", result)
		count++
		if count >= 3 {
			cancel2() // 3件処理したらパイプライン全体を停止
			break
		}
	}
	time.Sleep(20 * time.Millisecond) // goroutineのクリーンアップを待つ
	fmt.Println()
}

// ============================================================================
// 8. Rate Limiter - トークンバケットアルゴリズム
// ============================================================================
// 考えてほしい疑問:
//   - トークンバケットとリーキーバケットの違いは？
//   - バーストを許可するかしないかで設計がどう変わる？

// RateLimiter はチャネルベースのトークンバケット
type RateLimiter struct {
	tokens   chan struct{}
	ticker   *time.Ticker
	stopOnce sync.Once
	stopCh   chan struct{}
}

// NewRateLimiter は毎秒rateリクエスト、最大burstバーストのリミッターを生成
func NewRateLimiter(rate int, burst int) *RateLimiter {
	rl := &RateLimiter{
		tokens: make(chan struct{}, burst),
		ticker: time.NewTicker(time.Second / time.Duration(rate)),
		stopCh: make(chan struct{}),
	}

	// 初期トークンをバーストサイズ分充填
	for i := 0; i < burst; i++ {
		rl.tokens <- struct{}{}
	}

	// 定期的にトークンを補充するgoroutine
	go func() {
		for {
			select {
			case <-rl.stopCh:
				return
			case <-rl.ticker.C:
				select {
				case rl.tokens <- struct{}{}:
				default: // バケットが満杯なら捨てる
				}
			}
		}
	}()

	return rl
}

// Allow はトークンを1つ消費する。成功したらtrue
func (rl *RateLimiter) Allow() bool {
	select {
	case <-rl.tokens:
		return true
	default:
		return false
	}
}

// Wait はトークンが利用可能になるまでブロックする
func (rl *RateLimiter) Wait(ctx context.Context) error {
	select {
	case <-rl.tokens:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

// Stop はリミッターを停止する
func (rl *RateLimiter) Stop() {
	rl.stopOnce.Do(func() {
		rl.ticker.Stop()
		close(rl.stopCh)
	})
}

func demoRateLimiter() {
	fmt.Println("=== 8. Rate Limiter ===")

	// 毎秒20リクエスト、バースト5
	limiter := NewRateLimiter(20, 5)
	defer limiter.Stop()

	allowed := 0
	denied := 0

	// 15リクエストを一気に送る
	for i := 0; i < 15; i++ {
		if limiter.Allow() {
			allowed++
		} else {
			denied++
		}
	}
	fmt.Printf("  即時判定: 許可=%d, 拒否=%d (バースト5なので最初の5件が通る)\n", allowed, denied)

	// Waitで待機するパターン
	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	waitCount := 0
	for {
		if err := limiter.Wait(ctx); err != nil {
			break
		}
		waitCount++
	}
	fmt.Printf("  Wait待機: 200ms間に %d リクエスト処理\n", waitCount)
	fmt.Println()
}

// ============================================================================
// 9. Circuit Breaker - サーキットブレーカー
// ============================================================================
// 考えてほしい疑問:
//   - Half-Open状態で何件成功したらClosedに戻すべき？
//   - Circuit Breakerとリトライの組み合わせはどうすべき？
//   - マイクロサービスでCircuit Breakerがないとどんな障害が起きる？（カスケード障害）

// CircuitState はサーキットブレーカーの状態を表す
type CircuitState int

const (
	StateClosed   CircuitState = iota // 正常: リクエストを通す
	StateOpen                         // 遮断: リクエストを即座に拒否
	StateHalfOpen                     // 試行: 少数のリクエストだけ通す
)

func (s CircuitState) String() string {
	switch s {
	case StateClosed:
		return "CLOSED"
	case StateOpen:
		return "OPEN"
	case StateHalfOpen:
		return "HALF-OPEN"
	default:
		return "UNKNOWN"
	}
}

// CircuitBreaker はサーキットブレーカーパターンの実装
type CircuitBreaker struct {
	mu               sync.Mutex
	state            CircuitState
	failureCount     int
	successCount     int
	failureThreshold int           // この回数失敗したらOpenにする
	successThreshold int           // Half-Openでこの回数成功したらClosedに戻す
	timeout          time.Duration // Open状態の持続時間
	lastFailureTime  time.Time
}

// NewCircuitBreaker は新しいサーキットブレーカーを生成する
func NewCircuitBreaker(failureThreshold, successThreshold int, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		state:            StateClosed,
		failureThreshold: failureThreshold,
		successThreshold: successThreshold,
		timeout:          timeout,
	}
}

// Execute はサーキットブレーカーを通して関数を実行する
func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()

	switch cb.state {
	case StateOpen:
		// タイムアウト経過後ならHalf-Openに遷移
		if time.Since(cb.lastFailureTime) > cb.timeout {
			cb.state = StateHalfOpen
			cb.successCount = 0
			fmt.Printf("    [CB] OPEN → HALF-OPEN に遷移\n")
		} else {
			cb.mu.Unlock()
			return errors.New("circuit breaker is OPEN")
		}
	}
	cb.mu.Unlock()

	// 実際の関数を実行
	err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.failureCount++
		cb.lastFailureTime = time.Now()

		if cb.state == StateHalfOpen || cb.failureCount >= cb.failureThreshold {
			cb.state = StateOpen
			fmt.Printf("    [CB] → OPEN に遷移 (失敗数: %d)\n", cb.failureCount)
		}
		return err
	}

	// 成功
	if cb.state == StateHalfOpen {
		cb.successCount++
		if cb.successCount >= cb.successThreshold {
			cb.state = StateClosed
			cb.failureCount = 0
			fmt.Printf("    [CB] HALF-OPEN → CLOSED に遷移 (成功数: %d)\n", cb.successCount)
		}
	} else {
		cb.failureCount = 0 // 成功したらリセット
	}
	return nil
}

func demoCircuitBreaker() {
	fmt.Println("=== 9. Circuit Breaker ===")

	cb := NewCircuitBreaker(3, 2, 100*time.Millisecond)

	// 模擬サービス: 呼び出し回数で成功/失敗を切り替える
	var callCount int32

	callService := func() error {
		n := atomic.AddInt32(&callCount, 1)
		// 最初の5回は失敗、その後は成功
		if n <= 5 {
			return fmt.Errorf("service error (call #%d)", n)
		}
		return nil
	}

	// フェーズ1: 連続失敗 → Open
	for i := 0; i < 5; i++ {
		err := cb.Execute(callService)
		if err != nil {
			fmt.Printf("  呼び出し %d: エラー=%v, 状態=%s\n", i+1, err, cb.state)
		}
	}

	// フェーズ2: Open状態でリクエスト拒否
	err := cb.Execute(callService)
	fmt.Printf("  Open中の呼び出し: エラー=%v\n", err)

	// フェーズ3: タイムアウト待機後 → Half-Open → 成功 → Closed
	fmt.Println("  (100ms待機...)")
	time.Sleep(120 * time.Millisecond)

	for i := 0; i < 3; i++ {
		err := cb.Execute(callService)
		state := cb.state
		if err != nil {
			fmt.Printf("  リカバリ %d: エラー=%v, 状態=%s\n", i+1, err, state)
		} else {
			fmt.Printf("  リカバリ %d: 成功, 状態=%s\n", i+1, state)
		}
	}
	fmt.Println()
}

// ============================================================================
// 10. Graceful Shutdown - シグナル処理とコネクションドレイン
// ============================================================================
// 考えてほしい疑問:
//   - SIGTERMとSIGKILLの違いは？（SIGKILLはcatchできない）
//   - k8sのpreStopフックとGraceful Shutdownの関係は？
//   - シャットダウン中に新しいリクエストが来たらどうすべき？

func demoGracefulShutdown() {
	fmt.Println("=== 10. Graceful Shutdown ===")
	fmt.Println("  注: 実際のHTTPサーバーは起動しません（デモのため構造のみ）")

	// 実際のプロダクションコードの構造を示す
	// 本デモではgoroutineで短時間だけ動かす

	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintln(w, "OK")
	})
	mux.HandleFunc("/api/data", func(w http.ResponseWriter, r *http.Request) {
		// リクエストのcontextを使う（クライアント切断時に自動キャンセル）
		ctx := r.Context()
		select {
		case <-time.After(100 * time.Millisecond):
			fmt.Fprintln(w, `{"status":"ok"}`)
		case <-ctx.Done():
			http.Error(w, "request cancelled", http.StatusServiceUnavailable)
		}
	})

	server := &http.Server{
		Addr:         ":0", // テスト用にランダムポート
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful Shutdown のパターン（構造を示す）
	// 本来は実際にListenAndServeするが、デモでは構造のみ説明
	shutdownDemo := func() {
		// シグナルを待機するチャネル
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT)

		// サーバー起動（実際のコードではgo server.ListenAndServe()）
		fmt.Println("  [構造説明] サーバー起動")

		// シグナルまたはタイムアウトを待機
		// 本デモではタイムアウトでシミュレート
		select {
		case <-time.After(50 * time.Millisecond):
			fmt.Println("  [構造説明] シャットダウン開始（デモタイムアウト）")
		}

		// Graceful Shutdown
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()

		// 新しいリクエストの受付を停止し、処理中のリクエストが完了するまで待つ
		if err := server.Shutdown(ctx); err != nil {
			fmt.Printf("  シャットダウンエラー: %v\n", err)
		}
		// server.Shutdown が呼ばれるとclosedになるので形式上参照しておく
		_ = server

		signal.Stop(sigCh) // シグナル監視を停止

		fmt.Println("  [構造説明] サーバー正常終了")
	}

	shutdownDemo()

	// Graceful Shutdownの完全なコード（コメントで提示）
	fmt.Println()
	fmt.Println("  --- プロダクション用 Graceful Shutdown テンプレート ---")
	fmt.Println(`
  // func main() {
  //     server := &http.Server{Addr: ":8080", Handler: mux}
  //
  //     // サーバーを別goroutineで起動
  //     go func() {
  //         if err := server.ListenAndServe(); err != http.ErrServerClosed {
  //             log.Fatalf("HTTP server error: %v", err)
  //         }
  //     }()
  //
  //     // SIGTERM/SIGINTを待機
  //     sigCh := make(chan os.Signal, 1)
  //     signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT)
  //     <-sigCh
  //
  //     // 30秒のグレースフルシャットダウン
  //     ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
  //     defer cancel()
  //     server.Shutdown(ctx)
  // }`)
	fmt.Println()
}

// ============================================================================
// [実装してみよう] 課題一覧
// ============================================================================
func printExercises() {
	fmt.Println("============================================================")
	fmt.Println("[実装してみよう] 課題")
	fmt.Println("============================================================")
	exercises := []string{
		"1. Fan-out/Fan-inパターンで、URLのリストを並行にHTTP GETし、\n   レスポンスサイズの合計を計算する関数を実装せよ",
		"2. context.WithDeadline を使って、複数のAPI呼び出しに\n   「全体で3秒」の制限時間を設ける関数を実装せよ",
		"3. sync.RWMutex を使って、Read-Heavy なキャッシュ（LRU）を実装せよ\n   ヒント: container/list + map",
		"4. Worker Pool に動的スケーリング機能を追加せよ\n   （負荷に応じてワーカー数を増減させる）",
		"5. Rate Limiter に「スライディングウィンドウ」方式を追加実装せよ",
		"6. Circuit Breaker に「失敗率ベース」のトリップ条件を追加せよ\n   （例: 直近100リクエスト中50%以上が失敗したらOpen）",
		"7. Pipeline パターンで CSV → フィルタ → 集計 → JSON出力 の\n   4ステージパイプラインを実装せよ",
		"8. Graceful Shutdown に WebSocket コネクションのドレイン処理を追加せよ",
	}
	for _, ex := range exercises {
		fmt.Printf("  %s\n\n", ex)
	}
}

// ============================================================================
// main - 全デモを実行
// ============================================================================
func main() {
	fmt.Println("╔══════════════════════════════════════════════════════════╗")
	fmt.Println("║   Go 並行処理パターン - FAANG面接レベル完全ガイド       ║")
	fmt.Println("╚══════════════════════════════════════════════════════════╝")
	fmt.Println()

	demoFanOutFanIn()
	demoSelect()
	demoContext()
	demoSync()
	demoErrGroup()
	demoWorkerPool()
	demoPipeline()
	demoRateLimiter()
	demoCircuitBreaker()
	demoGracefulShutdown()
	printExercises()

	fmt.Println("全デモ完了!")
}
