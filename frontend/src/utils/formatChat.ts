/**
 * 轻量级 Markdown→HTML 转换，用于 AI 聊天消息格式化渲染。
 * 支持：代码块、行内代码、粗体、斜体、无序列表、有序列表、标题、段落、换行。
 */

function escapeHtml(text: string): string {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

export function formatChatContent(raw: string): string {
    if (!raw) return '';

    // 1. 提取围栏代码块（```lang\n...\n```）
    const codeBlocks: string[] = [];
    let text = raw.replace(/```(\w*)\n([\s\S]*?)```/g, (_match, lang, code) => {
        const idx = codeBlocks.length;
        const langLabel = lang ? `<span class="code-lang">${escapeHtml(lang)}</span>` : '';
        codeBlocks.push(
            `<div class="chat-code-block">${langLabel}<pre><code>${escapeHtml(code.replace(/\n$/, ''))}</code></pre></div>`
        );
        return `\x00CB${idx}\x00`;
    });

    // 2. 按空行分段
    const paragraphs = text.split(/\n{2,}/);
    const rendered = paragraphs.map((para) => {
        // 还原代码块占位
        if (/^\x00CB\d+\x00$/.test(para.trim())) {
            const idx = Number(para.trim().replace(/\x00CB|\x00/g, ''));
            return codeBlocks[idx] ?? '';
        }

        const lines = para.split('\n');

        // 检测无序列表
        if (lines.every((l) => /^\s*[-*•]\s/.test(l) || l.trim() === '')) {
            const items = lines
                .filter((l) => l.trim())
                .map((l) => `<li>${inlineFormat(l.replace(/^\s*[-*•]\s/, ''))}</li>`)
                .join('');
            return `<ul class="chat-list">${items}</ul>`;
        }

        // 检测有序列表
        if (lines.every((l) => /^\s*\d+[.)]\s/.test(l) || l.trim() === '')) {
            const items = lines
                .filter((l) => l.trim())
                .map((l) => `<li>${inlineFormat(l.replace(/^\s*\d+[.)]\s/, ''))}</li>`)
                .join('');
            return `<ol class="chat-list">${items}</ol>`;
        }

        // 标题
        const headingMatch = para.match(/^(#{1,3})\s+(.+)$/);
        if (headingMatch) {
            const level = headingMatch[1].length;
            return `<h${level + 2} class="chat-heading">${inlineFormat(headingMatch[2])}</h${level + 2}>`;
        }

        // 普通段落（保留单换行为 <br>）
        const formatted = lines.map((l) => inlineFormat(l)).join('<br/>');
        return `<p class="chat-para">${formatted}</p>`;
    });

    return rendered.join('');
}

/** 行内格式化：粗体、斜体、行内代码 */
function inlineFormat(line: string): string {
    let s = escapeHtml(line);
    // 行内代码
    s = s.replace(/`([^`]+)`/g, '<code class="chat-inline-code">$1</code>');
    // 粗体
    s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // 斜体
    s = s.replace(/\*(.+?)\*/g, '<em>$1</em>');
    return s;
}
