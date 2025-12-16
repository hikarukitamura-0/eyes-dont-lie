# **Web アプリケーション要件定義書**

プロジェクト名: Zone Key  
コンポーネント: Web ダッシュボード・クラウドプラットフォーム  
最終更新日: 2025-12-11

## **1. 概要**

Next.js + Supabase で構築する Web アプリケーション。ユーザーの生産性データを可視化し、環境相性の分析、タスク推奨、チーム管理機能を提供する。

## **2. 技術スタック**

### **2.1 フロントエンド**

| 技術              | バージョン        | 用途              |
| :---------------- | :---------------- | :---------------- |
| **Next.js**       | 14.x (App Router) | フレームワーク    |
| **React**         | 18.x              | UI ライブラリ     |
| **TypeScript**    | 5.x               | 型安全性          |
| **Tailwind CSS**  | 3.x               | スタイリング      |
| **shadcn/ui**     | latest            | UI コンポーネント |
| **Recharts**      | 2.x               | グラフ・可視化    |
| **Framer Motion** | latest            | アニメーション    |

### **2.2 バックエンド**

| 技術                   | 用途                           |
| :--------------------- | :----------------------------- |
| **Supabase**           | BaaS（認証・DB・リアルタイム） |
| **PostgreSQL**         | データベース                   |
| **Supabase Functions** | サーバーサイドロジック         |
| **Row Level Security** | データアクセス制御             |

### **2.3 インフラ**

| 技術               | 用途                       |
| :----------------- | :------------------------- |
| **Vercel**         | フロントエンドホスティング |
| **Supabase Cloud** | バックエンドホスティング   |

## **3. 機能要件**

### **3.1 認証・ユーザー管理**

#### **3.1.1 ユーザー登録・ログイン**

| 機能                   | 詳細                              |
| :--------------------- | :-------------------------------- |
| **メール認証**         | Supabase Auth を使用              |
| **SSO 対応**           | Google/GitHub OAuth（オプション） |
| **パスワードリセット** | メール経由でのリセット機能        |
| **セッション管理**     | JWT + リフレッシュトークン        |

#### **3.1.2 ユーザープロファイル**

```typescript
interface UserProfile {
	id: string;
	email: string;
	display_name: string;
	role: "user" | "admin";
	team_id?: string;
	created_at: Date;
	settings: {
		notifications_enabled: boolean;
		auto_task_recommendation: boolean;
		led_control_enabled: boolean;
	};
}
```

### **3.2 キャパシティ・タンク UI**

#### **3.2.1 コンセプト**

**加点法による「やりきった感」の可視化**

- 減点法（残タスク数）ではなく、加点法（達成量）を採用
- 仕事の密度と量に応じてタンクが満たされる
- 満タン（100%）で「本日の業務終了推奨」

#### **3.2.2 UI 仕様**

**タンク表示:**

```
┌─────────────────────┐
│                     │
│      🌟 100%       │ ← 満タン時: 金色に輝く
│  ██████████████    │ ← アニメーション: 波打つ
│  ██████████████    │
│  ██████████████    │
│                     │
│  本日の成果スコア   │
│   1,250 pts        │
└─────────────────────┘
```

**計算ロジック:**

```typescript
// タンク蓄積量の計算
const calculateTankLevel = (logs: ActivityLog[]): number => {
	let score = 0;

	logs.forEach((log) => {
		// 集中度が高いほど高ポイント
		const focusMultiplier = log.focus_score;

		// 作業密度（打鍵数、マウス動作）
		const activityIntensity = (log.keystrokes + log.mouse_distance) / 1000;

		// 作業カテゴリ別の重み
		const categoryWeight =
			{
				development: 1.5, // 開発作業は高評価
				communication: 1.0, // コミュニケーションは標準
				browsing: 0.5, // ブラウジングは低評価
			}[log.category] || 1.0;

		score += focusMultiplier * activityIntensity * categoryWeight;
	});

	// 1日の目標: 1500ポイント → 100%
	return Math.min((score / 1500) * 100, 100);
};
```

#### **3.2.3 インタラクション**

- タンクをホバーすると、内訳の詳細をツールチップ表示
- 100%到達時に祝福アニメーション + プッシュ通知
- 「早退推奨モード」を表示（管理者承認不要）

### **3.3 環境相性レポート**

#### **3.3.1 個人向けレポート画面**

**レイアウト:**

```
┌─────────────────────────────────────────┐
│ 🌡️ あなたの最適環境プロファイル        │
├─────────────────────────────────────────┤
│                                         │
│  最も集中できる条件:                    │
│  🔥 室温: 24.5℃ (±1.5℃)               │
│  💧 湿度: 50% (±10%)                   │
│  📊 気圧: 1013hPa                      │
│                                         │
│  集中力が持続しやすい時間帯:            │
│  🌅 09:00-11:00 (午前のゴールデンタイム)│
│  🌆 14:00-16:00 (午後の第2ピーク)      │
│                                         │
│  推奨座席エリア（フリーアドレス）:      │
│  🪑 A-3（窓際・南向き）                │
│  🪑 B-7（個室ブース）                  │
│                                         │
└─────────────────────────────────────────┘
```

#### **3.3.2 環境-集中度グラフ**

**3D ヒートマップ:**

- X 軸: 室温（18℃ ～ 28℃）
- Y 軸: 湿度（30%～ 70%）
- Z 軸（色）: 平均集中度スコア

**実装:**

```typescript
// Rechartsを使用した3Dヒートマップ
<ResponsiveContainer width='100%' height={400}>
	<ScatterChart>
		<XAxis dataKey='temperature' label='室温 (℃)' />
		<YAxis dataKey='humidity' label='湿度 (%)' />
		<ZAxis dataKey='focus_score' range={[0, 1]} />
		<Scatter data={environmentData} fill='#8884d8' />
	</ScatterChart>
</ResponsiveContainer>
```

#### **3.3.3 座席推奨アルゴリズム**

```typescript
interface SeatRecommendation {
	seat_id: string;
	score: number; // 0-100
	reasons: string[];
}

const recommendSeat = (
	userProfile: UserProfile,
	currentConditions: EnvironmentData[]
): SeatRecommendation[] => {
	return seats
		.map((seat) => {
			const seatCondition = currentConditions.find(
				(c) => c.seat_id === seat.id
			);

			// ユーザーの最適条件との差分を計算
			const tempDiff = Math.abs(
				seatCondition.temperature - userProfile.optimal_temp
			);
			const humidityDiff = Math.abs(
				seatCondition.humidity - userProfile.optimal_humidity
			);

			// スコア計算（差分が小さいほど高得点）
			const score = 100 - (tempDiff * 5 + humidityDiff * 0.5);

			return {
				seat_id: seat.id,
				score,
				reasons: [
					`室温 ${seatCondition.temperature}℃（最適値に近い）`,
					`静かなエリア（騒音レベル: 低）`,
				],
			};
		})
		.sort((a, b) => b.score - a.score);
};
```

### **3.4 予知保全ダッシュボード（管理者向け）**

#### **3.4.1 チームコンディション・ヒートマップ**

**表示内容:**

```
チーム「開発部」のコンディション推移（過去7日間）

        月   火   水   木   金   土   日
Alice   🟢  🟢  🟡  🟢  🔵  🔴  🟢
Bob     🔵  🔵  🔵  🟢  🟢  🟢  🟢
Carol   🟢  🟡  🔴  🔴  ⚠️  -   -
Dave    🟢  🟢  🟢  🟢  🟢  🟢  🟢

🔵 Deep Focus  🟢 Open  🟡 注意  🔴 要ケア  ⚠️ 緊急
```

**アラート機能:**

- 🔴 が 2 日連続 → 「要ケア」通知（管理者へメール）
- ⚠️ が発生 → 緊急アラート（即座に Slack/Teams 通知）
- チーム全体の平均集中度が低下 → 「環境改善推奨」

#### **3.4.2 プライバシー保護設計**

| データレベル             | 個人識別 | 管理者閲覧 | 表示内容                 |
| :----------------------- | :------- | :--------- | :----------------------- |
| **レベル 1: 個人詳細**   | ○        | ×          | 本人のみ閲覧可能         |
| **レベル 2: 匿名化集約** | ×        | ○          | 「メンバー A」として表示 |
| **レベル 3: チーム統計** | ×        | ○          | チーム平均値のみ         |

**実装:**

```sql
-- Row Level Security (RLS)
CREATE POLICY "管理者は匿名化データのみ閲覧可能"
ON activity_logs
FOR SELECT
USING (
  -- 本人は全データ閲覧可能
  auth.uid() = user_id
  OR
  -- 管理者は集約データのみ
  (
    is_admin(auth.uid())
    AND
    query_type = 'aggregated'
  )
);
```

#### **3.4.3 予測アラート機能**

**燃え尽き予測:**

```typescript
interface BurnoutPrediction {
	user_id: string;
	risk_level: "low" | "medium" | "high" | "critical";
	estimated_days_until_burnout: number;
	contributing_factors: string[];
	recommendations: string[];
}

// 予測ロジック
const predictBurnout = (userLogs: ActivityLog[]): BurnoutPrediction => {
	// 過去2週間のトレンド分析
	const trend = calculateFatigueTrend(userLogs);

	if (trend.slope > 0.5 && trend.avg_focus < 0.4) {
		return {
			user_id: userLogs[0].user_id,
			risk_level: "high",
			estimated_days_until_burnout: 5,
			contributing_factors: [
				"連続7日間の長時間労働（1日平均10時間）",
				"休憩取得頻度の低下（推奨の50%未満）",
				"集中度スコアの継続的低下",
			],
			recommendations: [
				"今週は定時退社を推奨",
				"軽めのタスクへの切り替え",
				"1on1面談の実施",
			],
		};
	}
	// ...
};
```

### **3.5 AI タスク・ナビゲーション**

#### **3.5.1 リアルタイム推奨タスク表示**

**通知 UI:**

```
┌─────────────────────────────────────┐
│ 🎯 Zone Key からの提案              │
├─────────────────────────────────────┤
│                                     │
│ 現在のコンディション:                │
│ 🔵 Deep Focus (集中度: 89%)        │
│                                     │
│ 推奨アクション:                      │
│ ✅ 今が「ゾーン」のチャンス！       │
│ 以下のタスクに集中してください:      │
│                                     │
│ 📝 新機能の設計書作成               │
│ 💻 難易度の高いコーディング          │
│ 🧠 アーキテクチャ検討               │
│                                     │
│ 通知をブロックしました 🔕           │
│                                     │
│ [了解] [後で通知]                   │
└─────────────────────────────────────┘
```

#### **3.5.2 タスク推奨ロジック**

```typescript
interface TaskRecommendation {
	task_type: "creative" | "routine" | "rest";
	priority: number;
	reason: string;
}

const recommendTask = (currentState: UserState): TaskRecommendation => {
	if (currentState.focus_score > 0.7) {
		return {
			task_type: "creative",
			priority: 10,
			reason: "高集中状態です。思考系タスクに最適です。",
		};
	} else if (currentState.focus_score > 0.3) {
		return {
			task_type: "routine",
			priority: 5,
			reason: "標準状態です。作業系タスクが適しています。",
		};
	} else {
		return {
			task_type: "rest",
			priority: 9,
			reason: "疲労が検出されました。10分間の休憩を推奨します。",
		};
	}
};
```

#### **3.5.3 通知ブロック機能**

**Deep Focus 時の自動制御:**

- Slack/Teams のステータスを「取り込み中」に変更（API 連携）
- OS の通知を一時停止（PC Agent と連携）
- カレンダーに「集中時間」ブロックを自動追加

### **3.6 データ可視化・レポート**

#### **3.6.1 日次レポート**

**表示項目:**

- タンク蓄積量の推移（時間軸グラフ）
- 集中度スコアの変動
- 作業カテゴリの内訳（円グラフ）
- 環境データの記録
- 達成したタスク数

**自動メール送信:**

- 毎日 18:00 に自動生成
- 「今日のハイライト」を要約
- 明日への改善提案

#### **3.6.2 週次/月次レポート**

**分析項目:**

- 平均集中時間の推移
- 最も生産性が高かった時間帯/曜日
- 環境条件と生産性の相関分析
- チーム比較（匿名化）
- 改善トレンド

### **3.7 設定・カスタマイズ**

#### **3.7.1 個人設定**

| 設定項目       | 選択肢                           | デフォルト   |
| :------------- | :------------------------------- | :----------- |
| **通知頻度**   | リアルタイム / 1 時間ごと / オフ | リアルタイム |
| **LED 制御**   | 自動 / 手動 / オフ               | 自動         |
| **タスク推奨** | 有効 / 無効                      | 有効         |
| **データ共有** | チームと共有 / プライベート      | チームと共有 |
| **勤務時間**   | カスタム設定                     | 09:00-18:00  |

#### **3.7.2 チーム設定（管理者）**

| 設定項目           | 詳細                       |
| :----------------- | :------------------------- |
| **アラート閾値**   | 「要ケア」判定の基準値設定 |
| **通知先**         | Slack/Teams Webhook URL    |
| **データ保持期間** | 30 日/90 日/1 年           |
| **匿名化レベル**   | 強/中/弱                   |

## **4. データベース設計**

### **4.1 テーブル構成**

#### **users テーブル**

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  display_name TEXT,
  role TEXT DEFAULT 'user',
  team_id UUID REFERENCES teams(id),
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### **activity_logs テーブル**

```sql
CREATE TABLE activity_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  timestamp TIMESTAMP NOT NULL,
  focus_score REAL,
  fatigue_prediction INTEGER,
  state TEXT,  -- 'deep_focus' | 'open' | 'overheat'
  keystroke_data JSONB,
  mouse_data JSONB,
  environment_data JSONB,
  work_category TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_activity_logs_user_timestamp
ON activity_logs(user_id, timestamp DESC);
```

#### **environment_profiles テーブル**

```sql
CREATE TABLE environment_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) UNIQUE,
  optimal_temperature REAL,
  optimal_humidity REAL,
  temperature_sensitivity REAL,
  best_time_slots TEXT[],
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **daily_summaries テーブル**

```sql
CREATE TABLE daily_summaries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  date DATE NOT NULL,
  tank_level REAL,
  total_score INTEGER,
  avg_focus_score REAL,
  deep_focus_minutes INTEGER,
  tasks_completed INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, date)
);
```

### **4.2 リアルタイム機能**

**Supabase Realtime を使用:**

```typescript
// クライアント側でリアルタイム更新を購読
const channel = supabase
	.channel("activity_updates")
	.on(
		"postgres_changes",
		{
			event: "INSERT",
			schema: "public",
			table: "activity_logs",
			filter: `user_id=eq.${userId}`,
		},
		(payload) => {
			// UIをリアルタイム更新
			updateDashboard(payload.new);
		}
	)
	.subscribe();
```

## **5. API 設計**

### **5.1 RESTful API**

#### **ログ送信 API**

```typescript
POST /api/logs
Content-Type: application/json
Authorization: Bearer {token}

{
  "timestamp": "2025-12-11T10:30:00Z",
  "focus_score": 0.85,
  "fatigue_prediction": 45,
  "state": "deep_focus",
  "keystroke_data": { ... },
  "environment_data": { ... }
}

Response: 201 Created
{
  "id": "uuid",
  "status": "success"
}
```

#### **環境相性取得 API**

```typescript
GET /api/environment-profile
Authorization: Bearer {token}

Response: 200 OK
{
  "optimal_temperature": 24.5,
  "optimal_humidity": 50.0,
  "best_time_slots": ["09:00-11:00", "14:00-16:00"],
  "recommended_seats": [
    { "seat_id": "A-3", "score": 95 }
  ]
}
```

### **5.2 Supabase Edge Functions**

**日次サマリー生成:**

```typescript
// supabase/functions/generate-daily-summary/index.ts
Deno.serve(async (req) => {
	const { userId, date } = await req.json();

	// ログデータを集計
	const logs = await supabaseClient
		.from("activity_logs")
		.select("*")
		.eq("user_id", userId)
		.gte("timestamp", `${date}T00:00:00`)
		.lt("timestamp", `${date}T23:59:59`);

	// サマリーを計算
	const summary = calculateDailySummary(logs.data);

	// DBに保存
	await supabaseClient.from("daily_summaries").insert(summary);

	return new Response(JSON.stringify(summary), {
		headers: { "Content-Type": "application/json" },
	});
});
```

## **6. UI/UX デザイン指針**

### **6.1 デザインコンセプト**

**キーワード:**

- モダン・ミニマル
- 心理的安全性（監視感の排除）
- ゲーミフィケーション（達成感）
- データドリブンな美しさ

### **6.2 カラーパレット**

```css
:root {
	/* 状態カラー */
	--deep-focus: #3b82f6; /* 青 */
	--open: #10b981; /* 緑 */
	--overheat: #ef4444; /* 赤 */

	/* アクセント */
	--gold: #f59e0b; /* タンク満タン時 */
	--purple: #8b5cf6; /* プレミアム機能 */

	/* ニュートラル */
	--bg-primary: #0f172a; /* ダークモード背景 */
	--bg-secondary: #1e293b;
	--text-primary: #f1f5f9;
	--text-secondary: #94a3b8;
}
```

### **6.3 アニメーション**

- タンク蓄積: スムーズな上昇アニメーション（ease-out, 800ms）
- 状態変化: フェード + スケール（300ms）
- 通知表示: スライドイン（bottom to top, 400ms）
- 満タン達成: 紙吹雪エフェクト（Confetti.js）

## **7. パフォーマンス要件**

| 指標                     | 目標値                          |
| :----------------------- | :------------------------------ |
| **初回ロード時間**       | < 2 秒（Lighthouse Score > 90） |
| **Time to Interactive**  | < 3 秒                          |
| **データ更新レイテンシ** | < 500ms（Supabase Realtime）    |
| **API 応答時間**         | < 200ms（P95）                  |
| **同時接続ユーザー**     | 1000 人（初期スケール）         |

## **8. セキュリティ要件**

| 項目             | 対策                                     |
| :--------------- | :--------------------------------------- |
| **認証**         | Supabase Auth（JWT） + MFA（オプション） |
| **データ暗号化** | TLS 1.3（通信）、AES-256（保存）         |
| **アクセス制御** | Row Level Security（RLS）                |
| **API 保護**     | Rate Limiting（100 req/min/user）        |
| **プライバシー** | GDPR 準拠、データ削除権の実装            |

## **9. テスト要件**

### **9.1 単体テスト**

- Vitest でコンポーネントテスト
- カバレッジ > 80%

### **9.2 E2E テスト**

- Playwright で主要フロー検証
- ログイン → ダッシュボード閲覧 → レポート生成

### **9.3 負荷テスト**

- k6 で API 負荷テスト
- 目標: 1000 req/s を安定処理

## **10. 実装優先順位**

### **Phase 1: MVP（2 週間）**

- [ ] 認証機能（Supabase Auth）
- [ ] 基本ダッシュボード（タンク UI）
- [ ] ログ受信 API
- [ ] 日次レポート表示

### **Phase 2: コア機能（2 週間）**

- [ ] 環境相性レポート
- [ ] リアルタイム更新（Supabase Realtime）
- [ ] タスク推奨通知
- [ ] 週次レポート

### **Phase 3: 管理者機能（1 週間）**

- [ ] チームダッシュボード
- [ ] 予知保全アラート
- [ ] 匿名化処理

### **Phase 4: 高度化（継続）**

- [ ] 座席推奨アルゴリズム
- [ ] Slack/Teams 連携
- [ ] モバイルアプリ（PWA）

