#!/usr/bin/env python3
"""
AGStock Community Features
ユーザーコミュニティ機能と戦略共有システム
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import uuid
import sqlite3
from dataclasses import dataclass, asdict
import plotly.graph_objects as go
import plotly.express as px
import base64


@dataclass
class User:
    """ユーザーデータクラス"""

    user_id: str
    username: str
    email: str
    join_date: datetime
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    reputation: int = 0
    strategies_shared: int = 0
    followers_count: int = 0
    following_count: int = 0


@dataclass
class Strategy:
    """戦略データクラス"""

    strategy_id: str
    author_id: str
    title: str
    description: str
    code: str
    category: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    upvotes: int = 0
    downvotes: int = 0
    views: int = 0
    comments_count: int = 0
    performance_score: Optional[float] = None
    is_public: bool = True


@dataclass
class Comment:
    """コメントデータクラス"""

    comment_id: str
    strategy_id: str
    author_id: str
    content: str
    created_at: datetime
    upvotes: int = 0
    downvotes: int = 0
    parent_id: Optional[str] = None


@dataclass
class Vote:
    """投票データクラス"""

    vote_id: str
    user_id: str
    target_id: str  # strategy_id or comment_id
    target_type: str  # 'strategy' or 'comment'
    vote_type: int  # 1 for upvote, -1 for downvote
    created_at: datetime


class CommunityDatabase:
    """コミュニティデータベース管理"""

    def __init__(self, db_path: str = "data/community.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()

    def init_database(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # ユーザーテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    join_date TIMESTAMP,
                    avatar_url TEXT,
                    bio TEXT,
                    reputation INTEGER DEFAULT 0,
                    strategies_shared INTEGER DEFAULT 0,
                    followers_count INTEGER DEFAULT 0,
                    following_count INTEGER DEFAULT 0
                )
            """)

            # 戦略テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    strategy_id TEXT PRIMARY KEY,
                    author_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    code TEXT,
                    category TEXT,
                    tags TEXT,  -- JSON形式
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    upvotes INTEGER DEFAULT 0,
                    downvotes INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    comments_count INTEGER DEFAULT 0,
                    performance_score REAL,
                    is_public BOOLEAN DEFAULT 1,
                    FOREIGN KEY (author_id) REFERENCES users (user_id)
                )
            """)

            # コメントテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    comment_id TEXT PRIMARY KEY,
                    strategy_id TEXT,
                    author_id TEXT,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP,
                    upvotes INTEGER DEFAULT 0,
                    downvotes INTEGER DEFAULT 0,
                    parent_id TEXT,
                    FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id),
                    FOREIGN KEY (author_id) REFERENCES users (user_id)
                )
            """)

            # 投票テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    vote_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    target_id TEXT,
                    target_type TEXT,
                    vote_type INTEGER,
                    created_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # フォロー関係テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follows (
                    follower_id TEXT,
                    following_id TEXT,
                    created_at TIMESTAMP,
                    PRIMARY KEY (follower_id, following_id),
                    FOREIGN KEY (follower_id) REFERENCES users (user_id),
                    FOREIGN KEY (following_id) REFERENCES users (user_id)
                )
            """)

            conn.commit()

    def create_user(self, username: str, email: str) -> User:
        """ユーザー作成"""
        user_id = str(uuid.uuid4())
        join_date = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users 
                (user_id, username, email, join_date)
                VALUES (?, ?, ?, ?)
            """,
                (user_id, username, email, join_date),
            )
            conn.commit()

        return User(
            user_id=user_id, username=username, email=email, join_date=join_date
        )

    def get_user(self, user_id: str = None, username: str = None) -> Optional[User]:
        """ユーザー取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if user_id:
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            elif username:
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            else:
                return None

            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                user_data = dict(zip(columns, row))
                return User(**user_data)

        return None

    def create_strategy(
        self,
        author_id: str,
        title: str,
        description: str,
        code: str,
        category: str,
        tags: List[str],
    ) -> Strategy:
        """戦略作成"""
        strategy_id = str(uuid.uuid4())
        created_at = datetime.now()
        updated_at = created_at

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO strategies 
                (strategy_id, author_id, title, description, code, category, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    strategy_id,
                    author_id,
                    title,
                    description,
                    code,
                    category,
                    json.dumps(tags),
                    created_at,
                    updated_at,
                ),
            )

            # ユーザーの戦略共有数を更新
            cursor.execute(
                """
                UPDATE users SET strategies_shared = strategies_shared + 1
                WHERE user_id = ?
            """,
                (author_id,),
            )

            conn.commit()

        return Strategy(
            strategy_id=strategy_id,
            author_id=author_id,
            title=title,
            description=description,
            code=code,
            category=category,
            tags=tags,
            created_at=created_at,
            updated_at=updated_at,
        )

    def get_strategies(
        self, category: str = None, limit: int = 20, sort_by: str = "created_at"
    ) -> List[Strategy]:
        """戦略リスト取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT * FROM strategies WHERE is_public = 1
            """
            params = []

            if category:
                query += " AND category = ?"
                params.append(category)

            if sort_by == "upvotes":
                query += " ORDER BY upvotes DESC"
            elif sort_by == "performance":
                query += " ORDER BY performance_score DESC NULLS LAST"
            else:
                query += " ORDER BY created_at DESC"

            query += " LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            strategies = []
            for row in rows:
                columns = [description[0] for description in cursor.description]
                strategy_data = dict(zip(columns, row))
                strategy_data["tags"] = json.loads(strategy_data["tags"])
                strategies.append(Strategy(**strategy_data))

            return strategies

    def vote_strategy(self, user_id: str, strategy_id: str, vote_type: int):
        """戦略への投票"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 既存の投票を確認
            cursor.execute(
                """
                SELECT * FROM votes 
                WHERE user_id = ? AND target_id = ? AND target_type = 'strategy'
            """,
                (user_id, strategy_id),
            )

            existing_vote = cursor.fetchone()

            if existing_vote:
                # 投票更新
                old_vote_type = existing_vote[4]  # vote_type column
                if old_vote_type != vote_type:
                    # 投票タイプが変更された場合
                    cursor.execute(
                        """
                        UPDATE votes SET vote_type = ?, created_at = ?
                        WHERE user_id = ? AND target_id = ? AND target_type = 'strategy'
                    """,
                        (vote_type, datetime.now(), user_id, strategy_id),
                    )

                    # 戦略の投票数を更新
                    if vote_type == 1:  # upvote
                        cursor.execute(
                            """
                            UPDATE strategies 
                            SET upvotes = upvotes + 1, downvotes = downvotes - 1
                            WHERE strategy_id = ?
                        """,
                            (strategy_id,),
                        )
                    else:  # downvote
                        cursor.execute(
                            """
                            UPDATE strategies 
                            SET upvotes = upvotes - 1, downvotes = downvotes + 1
                            WHERE strategy_id = ?
                        """,
                            (strategy_id,),
                        )
            else:
                # 新規投票
                vote_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO votes 
                    (vote_id, user_id, target_id, target_type, vote_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        vote_id,
                        user_id,
                        strategy_id,
                        "strategy",
                        vote_type,
                        datetime.now(),
                    ),
                )

                # 戦略の投票数を更新
                if vote_type == 1:  # upvote
                    cursor.execute(
                        """
                        UPDATE strategies SET upvotes = upvotes + 1 WHERE strategy_id = ?
                    """,
                        (strategy_id,),
                    )
                else:  # downvote
                    cursor.execute(
                        """
                        UPDATE strategies SET downvotes = downvotes + 1 WHERE strategy_id = ?
                    """,
                        (strategy_id,),
                    )

                # 作者の評価を更新
                cursor.execute(
                    """
                    UPDATE users SET reputation = reputation + ?
                    WHERE user_id = (SELECT author_id FROM strategies WHERE strategy_id = ?)
                """,
                    (vote_type, strategy_id),
                )

            conn.commit()


class CommunityDashboard:
    """コミュニティダッシュボード"""

    def __init__(self):
        self.db = CommunityDatabase()
        self.current_user = None

    def login_user(self, username: str) -> Optional[User]:
        """ユーザーログイン（簡単なデモ用）"""
        user = self.db.get_user(username=username)
        if user:
            self.current_user = user
            return user
        return None

    def register_user(self, username: str, email: str) -> User:
        """ユーザー登録"""
        user = self.db.create_user(username, email)
        self.current_user = user
        return user

    def display_leaderboard(self):
        """リーダーボード表示"""
        st.subheader("🏆 コミュニティリーダーボード")

        # 上位ユーザー取得
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, reputation, strategies_shared, join_date
                FROM users
                ORDER BY reputation DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()

        if rows:
            df = pd.DataFrame(
                rows, columns=["ユーザー名", "評価", "戦略共有数", "参加日"]
            )
            df["参加日"] = pd.to_datetime(df["参加日"]).dt.strftime("%Y-%m-%d")

            # ランキング表示
            for i, (_, row) in enumerate(df.iterrows(), 1):
                medal = (
                    "🥇"
                    if i == 1
                    else "🥈"
                    if i == 2
                    else "🥉"
                    if i == 3
                    else f"{i:2d}."
                )
                st.write(
                    f"{medal} **{row['ユーザー名']}** - 評価: {row['評価']} - 戦略: {row['戦略共有数']}"
                )

    def display_strategy_list(self):
        """戦略リスト表示"""
        st.subheader("📈 戦略ライブラリ")

        # フィルター
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            categories = [
                "すべて",
                "テクニカル分析",
                "ファンダメンタル分析",
                "AI機械学習",
                "リスク管理",
                "その他",
            ]
            selected_category = st.selectbox("カテゴリ", categories)

        with col2:
            sort_options = ["作成日順", "評価順", "パフォーマンス順"]
            sort_by_map = {
                "作成日順": "created_at",
                "評価順": "upvotes",
                "パフォーマンス順": "performance",
            }
            selected_sort = st.selectbox("並び替え", sort_options)

        with col3:
            if st.button("🔄 更新"):
                st.rerun()

        # 戦略取得
        category_filter = None if selected_category == "すべて" else selected_category
        sort_by = sort_by_map[selected_sort]
        strategies = self.db.get_strategies(category=category_filter, sort_by=sort_by)

        if strategies:
            for strategy in strategies:
                # 戦略カード
                author = self.db.get_user(user_id=strategy.author_id)
                author_name = author.username if author else "不明"

                # タグ表示
                tags_html = " ".join(
                    [
                        f'<span style="background:#e1f5fe; padding:2px 8px; border-radius:12px; font-size:12px; margin:2px;">{tag}</span>'
                        for tag in strategy.tags
                    ]
                )

                st.markdown(
                    f"""
                <div style="border:1px solid #ddd; border-radius:8px; padding:15px; margin:10px 0;">
                    <h4>{strategy.title}</h4>
                    <p style="color:#666; margin:5px 0;">by {author_name} • {strategy.created_at.strftime("%Y-%m-%d")}</p>
                    <p>{strategy.description[:200]}...</p>
                    <div style="margin:10px 0;">{tags_html}</div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            👍 {strategy.upvotes} 👎 {strategy.downvotes} 👁️ {strategy.views} 💬 {strategy.comments_count}
                        </div>
                        <div>
                            {f"⭐ パフォーマンス: {strategy.performance_score:.2f}" if strategy.performance_score else ""}
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # 詳細表示ボタン
                if st.button(f"詳細を見る", key=f"view_{strategy.strategy_id}"):
                    self.display_strategy_detail(strategy)
        else:
            st.info("戦略がありません")

    def display_strategy_detail(self, strategy: Strategy):
        """戦略詳細表示"""
        author = self.db.get_user(user_id=strategy.author_id)

        st.markdown(f"### {strategy.title}")
        st.write(f"投稿者: {author.username if author else '不明'}")
        st.write(f"投稿日: {strategy.created_at.strftime('%Y-%m-%d %H:%M')}")
        st.write(f"カテゴリ: {strategy.category}")

        # タグ
        tags_str = ", ".join(strategy.tags)
        st.write(f"タグ: {tags_str}")

        # 評価
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👍 いいね", strategy.upvotes)
        with col2:
            st.metric("👎 うーん", strategy.downvotes)
        with col3:
            st.metric("👁️ 閲覧数", strategy.views)
        with col4:
            st.metric("💬 コメント", strategy.comments_count)

        # 説明
        st.subheader("説明")
        st.write(strategy.description)

        # コード
        if strategy.code:
            st.subheader("戦略コード")
            st.code(strategy.code, language="python")

        # 投票機能
        if self.current_user:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 いいね", key=f"upvote_{strategy.strategy_id}"):
                    self.db.vote_strategy(
                        self.current_user.user_id, strategy.strategy_id, 1
                    )
                    st.success("いいねしました！")
                    st.rerun()

            with col2:
                if st.button("👎 うーん", key=f"downvote_{strategy.strategy_id}"):
                    self.db.vote_strategy(
                        self.current_user.user_id, strategy.strategy_id, -1
                    )
                    st.info("投票しました")
                    st.rerun()

    def create_strategy_form(self):
        """戦略作成フォーム"""
        st.subheader("✨ 新しい戦略を共有")

        with st.form("create_strategy"):
            title = st.text_input("戦略タイトル*", max_chars=100)
            category = st.selectbox(
                "カテゴリ*",
                [
                    "テクニカル分析",
                    "ファンダメンタル分析",
                    "AI機械学習",
                    "リスク管理",
                    "その他",
                ],
            )

            # タグ入力
            tag_input = st.text_input(
                "タグ（カンマ区切り）*", placeholder="例: 移動平均線, RSI, AI"
            )
            tags = (
                [tag.strip() for tag in tag_input.split(",") if tag.strip()]
                if tag_input
                else []
            )

            description = st.text_area(
                "説明*", height=150, help="戦略の概要や特徴を説明してください"
            )
            code = st.text_area(
                "戦略コード", height=300, help="Pythonコードを貼り付けてください"
            )

            is_public = st.checkbox(
                "公開する", value=True, help="チェックを外すと非公開になります"
            )

            submitted = st.form_submit_button("戦略を投稿")

            if submitted:
                if not title or not description:
                    st.error("タイトルと説明は必須です")
                elif self.current_user:
                    try:
                        strategy = self.db.create_strategy(
                            author_id=self.current_user.user_id,
                            title=title,
                            description=description,
                            code=code,
                            category=category,
                            tags=tags,
                        )

                        if not is_public:
                            # 非公開設定（実装は省略）
                            pass

                        st.success("✅ 戦略を投稿しました！")
                        st.rerun()

                    except Exception as e:
                        st.error(f"投稿エラー: {e}")
                else:
                    st.error("ログインが必要です")


def main():
    """メイン実行"""
    st.set_page_config(page_title="AGStock Community", page_icon="👥", layout="wide")

    # コミュニティダッシュボード初期化
    dashboard = CommunityDashboard()

    # サイドバー：ユーザー認証
    with st.sidebar:
        st.title("👤 ユーザー")

        if not dashboard.current_user:
            # ログイン/登録
            tab1, tab2 = st.tabs(["ログイン", "新規登録"])

            with tab1:
                username = st.text_input("ユーザー名")
                login_button = st.button("ログイン")

                if login_button and username:
                    user = dashboard.login_user(username)
                    if user:
                        st.success(f"ようこそ、{user.username}さん！")
                        st.rerun()
                    else:
                        st.error("ユーザーが見つかりません")

            with tab2:
                new_username = st.text_input("新しいユーザー名")
                new_email = st.text_input("メールアドレス")
                register_button = st.button("登録")

                if register_button and new_username and new_email:
                    try:
                        user = dashboard.register_user(new_username, new_email)
                        st.success(f"登録完了！ようこそ、{user.username}さん！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"登録エラー: {e}")
        else:
            # ログイン済み
            user = dashboard.current_user
            st.write(f"👤 {user.username}")
            st.write(f"評価: {user.reputation}")
            st.write(f"戦略数: {user.strategies_shared}")

            if st.button("ログアウト"):
                dashboard.current_user = None
                st.rerun()

    # メインコンテンツ
    st.title("🌐 AGStock コミュニティ")
    st.markdown("---")

    # ナビゲーションタブ
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 戦略ライブラリ", "🏆 リーダーボード", "✨ 戦略投稿", "📊 統計"]
    )

    with tab1:
        dashboard.display_strategy_list()

    with tab2:
        dashboard.display_leaderboard()

    with tab3:
        if dashboard.current_user:
            dashboard.create_strategy_form()
        else:
            st.warning("戦略を投稿するにはログインが必要です")

    with tab4:
        st.subheader("📊 コミュニティ統計")

        # 統計情報表示
        with sqlite3.connect(dashboard.db.db_path) as conn:
            cursor = conn.cursor()

            # ユーザー数
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            # 戦略数
            cursor.execute("SELECT COUNT(*) FROM strategies")
            total_strategies = cursor.fetchone()[0]

            # コメント数
            cursor.execute("SELECT COUNT(*) FROM comments")
            total_comments = cursor.fetchone()[0]

            # 投票数
            cursor.execute("SELECT COUNT(*) FROM votes")
            total_votes = cursor.fetchone()[0]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 ユーザー数", total_users)
        with col2:
            st.metric("📈 戦略数", total_strategies)
        with col3:
            st.metric("💬 コメント数", total_comments)
        with col4:
            st.metric("🗳️ 投票数", total_votes)

        # カテゴリ別戦略数
        st.subheader("カテゴリ別戦略数")
        with sqlite3.connect(dashboard.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM strategies
                WHERE is_public = 1
                GROUP BY category
                ORDER BY count DESC
            """)
            category_data = cursor.fetchall()

        if category_data:
            df = pd.DataFrame(category_data, columns=["カテゴリ", "戦略数"])
            fig = px.bar(df, x="カテゴリ", y="戦略数", title="カテゴリ別戦略分布")
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
