import type { AgentTrace } from '@/types'

export function createInitialTrace(): AgentTrace {
  return {
    steps: [
      {
        id: 'intent',
        title: '理解问题',
        detail: '等待识别问题意图与知识范围',
        status: 'pending',
      },
      {
        id: 'retrieve',
        title: '检索知识库',
        detail: '等待执行混合检索',
        status: 'pending',
      },
      {
        id: 'rerank',
        title: '证据重排',
        detail: '等待对候选片段进行相关性重排',
        status: 'pending',
      },
      {
        id: 'compose',
        title: '组织回答',
        detail: '等待基于证据生成可溯源回答',
        status: 'pending',
      },
    ],
    tools: [],
    chunks: [],
  }
}
