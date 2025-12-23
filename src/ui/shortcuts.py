"""
Keyboard Shortcuts System
Provides keyboard navigation and quick actions for power users.
"""

import streamlit as st
from streamlit.components.v1 import html
from typing import Dict, Callable, Optional


class KeyboardShortcuts:
    """Manages keyboard shortcuts for the application."""
    
    # Shortcut definitions
    SHORTCUTS: Dict[str, Dict[str, str]] = {
        # Navigation
        'Ctrl+1': {'action': 'goto_dashboard', 'description': 'ダッシュボードへ移動'},
        'Ctrl+2': {'action': 'goto_ai_center', 'description': 'AI分析センターへ移動'},
        'Ctrl+3': {'action': 'goto_trading', 'description': 'トレーディングへ移動'},
        'Ctrl+4': {'action': 'goto_lab', 'description': '戦略研究所へ移動'},
        'Ctrl+5': {'action': 'goto_mission_control', 'description': 'Mission Controlへ移動'},
        
        # Actions
        'Ctrl+S': {'action': 'run_scan', 'description': '市場スキャンを実行'},
        'Ctrl+P': {'action': 'open_portfolio', 'description': 'ポートフォリオを開く'},
        'Ctrl+R': {'action': 'refresh_data', 'description': 'データを更新'},
        
        # UI
        '/': {'action': 'focus_search', 'description': '検索にフォーカス'},
        '?': {'action': 'show_shortcuts', 'description': 'ショートカット一覧を表示'},
        'Esc': {'action': 'close_modal', 'description': 'モーダルを閉じる'},
    }
    
    @classmethod
    def inject_listener(cls):
        """Inject JavaScript keyboard listener into the page."""
        
        # Build JavaScript shortcuts map
        js_shortcuts = {}
        for key, config in cls.SHORTCUTS.items():
            js_shortcuts[key] = config['action']
        
        js_code = f"""
        <script>
        // Keyboard shortcuts listener
        const shortcuts = {js_shortcuts};
        
        document.addEventListener('keydown', function(e) {{
            // Build key combination string
            let key = '';
            if (e.ctrlKey) key += 'Ctrl+';
            if (e.shiftKey) key += 'Shift+';
            if (e.altKey) key += 'Alt+';
            
            // Add the actual key
            if (e.key.length === 1) {{
                key += e.key.toUpperCase();
            }} else {{
                key += e.key;
            }}
            
            // Check if this is a registered shortcut
            if (shortcuts[key]) {{
                e.preventDefault();
                
                // Send message to Streamlit
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    data: {{
                        action: shortcuts[key],
                        key: key
                    }}
                }}, '*');
                
                // Also store in session storage for Streamlit to read
                sessionStorage.setItem('keyboard_action', shortcuts[key]);
                
                // Trigger a rerun by clicking a hidden button
                const triggerBtn = document.getElementById('shortcut-trigger');
                if (triggerBtn) {{
                    triggerBtn.click();
                }}
            }}
        }});
        
        console.log('AGStock keyboard shortcuts loaded');
        </script>
        """
        
        html(js_code, height=0)
    
    @classmethod
    def render_help_panel(cls):
        """Render the keyboard shortcuts help panel."""
        st.markdown("### ⌨️ キーボードショートカット")
        
        # Group shortcuts by category
        categories = {
            'ナビゲーション': ['Ctrl+1', 'Ctrl+2', 'Ctrl+3', 'Ctrl+4', 'Ctrl+5'],
            'アクション': ['Ctrl+S', 'Ctrl+P', 'Ctrl+R'],
            'UI操作': ['/', '?', 'Esc'],
        }
        
        for category, keys in categories.items():
            st.markdown(f"**{category}**")
            
            for key in keys:
                if key in cls.SHORTCUTS:
                    config = cls.SHORTCUTS[key]
                    st.markdown(f"- `{key}`: {config['description']}")
            
            st.markdown("")
    
    @classmethod
    def get_action(cls) -> Optional[str]:
        """Get the last triggered keyboard action."""
        # Check session state for keyboard action
        if 'keyboard_action' not in st.session_state:
            st.session_state.keyboard_action = None
        
        action = st.session_state.keyboard_action
        
        # Clear the action after reading
        if action:
            st.session_state.keyboard_action = None
        
        return action
    
    @classmethod
    def handle_shortcuts(cls, handlers: Dict[str, Callable]):
        """
        Handle keyboard shortcuts with custom handlers.
        
        Args:
            handlers: Dict mapping action names to handler functions
        """
        action = cls.get_action()
        
        if action and action in handlers:
            handlers[action]()


def render_shortcut_badge(shortcut: str, description: str):
    """
    Render a keyboard shortcut badge.
    
    Args:
        shortcut: Keyboard shortcut (e.g., "Ctrl+S")
        description: Description of the action
    """
    badge_html = f"""
    <div style="
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: #1E2530;
        border: 1px solid #2D3748;
        border-radius: 0.5rem;
        padding: 0.25rem 0.75rem;
        margin: 0.25rem;
    ">
        <kbd style="
            background: #0E1117;
            border: 1px solid #2D3748;
            border-radius: 0.25rem;
            padding: 0.125rem 0.5rem;
            font-family: monospace;
            font-size: 0.875rem;
            color: #00D9FF;
        ">{shortcut}</kbd>
        <span style="color: #B0B0B0; font-size: 0.875rem;">{description}</span>
    </div>
    """
    
    st.markdown(badge_html, unsafe_allow_html=True)
