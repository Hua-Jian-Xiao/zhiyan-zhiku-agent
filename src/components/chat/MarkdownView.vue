<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import { escapeHtml } from '@/utils/format'

const props = withDefaults(
  defineProps<{
    content: string
    streaming?: boolean
  }>(),
  {
    streaming: false,
  },
)

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: true,
  highlight(code, language) {
    if (language && hljs.getLanguage(language)) {
      const highlighted = hljs.highlight(code, {
        language,
        ignoreIllegals: true,
      }).value
      return `<pre class="hljs"><code class="language-${escapeHtml(language)}">${highlighted}</code></pre>`
    }
    return `<pre class="hljs"><code>${escapeHtml(code)}</code></pre>`
  },
})

const defaultLinkOpen = md.renderer.rules.link_open
md.renderer.rules.link_open = (tokens, index, options, env, self) => {
  tokens[index]?.attrSet('target', '_blank')
  tokens[index]?.attrSet('rel', 'noopener noreferrer')
  if (defaultLinkOpen) return defaultLinkOpen(tokens, index, options, env, self)
  return self.renderToken(tokens, index, options)
}

const rendered = computed(() => md.render(props.content))
</script>

<template>
  <div
    class="markdown-body"
    :class="{ 'is-streaming': streaming }"
    v-html="rendered"
  />
</template>

<style scoped>
.markdown-body.is-streaming > :last-child::after {
  display: inline-block;
  width: 5px;
  height: 1.05em;
  margin-left: 3px;
  vertical-align: -0.16em;
  content: '';
  background: #7d302f;
  border-radius: 2px;
  animation: markdown-caret 0.95s steps(2, start) infinite;
}

@keyframes markdown-caret {
  50% {
    opacity: 0;
  }
}
</style>
