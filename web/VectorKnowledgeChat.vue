<template>
  <div class="vector-chat-container" :class="{ 'embedded': isEmbedded }">
    <div class="chat-header" v-if="!isEmbedded">
      <h2>{{ title }}</h2>
      <div class="stats-info" v-if="statistics">
        <span>文档数: {{ statistics.total_documents }}</span>
      </div>
    </div>
    
    <div class="chat-messages">
      <div v-for="(message, index) in messages" :key="index" class="message-wrapper">
        <div :class="['message', message.role]">
          <div class="message-avatar">{{ message.role === 'user' ? '用户' : 'AI' }}</div>
          <div class="message-content">
            <p>{{ message.content }}</p>
            <div v-if="message.documents && message.documents.length > 0" class="message-sources">
              <small>参考文档: {{ message.documents.length }} 篇</small>
            </div>
          </div></div>
      </div>
      <div v-if="isLoading" class="message-wrapper">
        <div class="message ai">
          <div class="message-avatar">AI</div>
          <div class="message-content">
            <div class="loading-indicator">
              <span class="loading-dot"></span>
              <span class="loading-dot"></span>
              <span class="loading-dot"></span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chat-input">
      <div class="date-filter" v-if="enableDateFilter">
        <input type="date" v-model="startDate" placeholder="开始日期">
        <span>至</span>
        <input type="date" v-model="endDate" placeholder="结束日期">
      </div>
      <div class="input-wrapper">
        <input
          type="text"
          v-model="userInput"
          @keyup.enter="sendMessage"
          placeholder="请输入您的问题... (输入'stats'查看统计信息，'clear'清空历史)"
          :disabled="isLoading"
        >
        <button @click="sendMessage" :disabled="isLoading || !userInput.trim()">
          发送
        </button>
      </div>
      <div class="chat-tips" v-if="!isEmbedded">
        <small>提示: 输入 'stats' 查看统计信息，'clear' 清空对话历史</small>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VectorKnowledgeChat',
  props: {
    title: {
      type: String,
      default: '向量数据库知识对话'
    },
    apiBaseUrl: {
      type: String,
      default: 'http://localhost:5001/api'
    },
    sessionId: {
      type: String,
      default: 'default'
    },
    enableDateFilter: {
      type: Boolean,
      default: true
    },
    isEmbedded: {
      type: Boolean,
      default: false
    },
    // 初始化参数
    initParams: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      messages: [],
      userInput: '',
      isLoading: false,
      startDate: '',
      endDate: '',
      statistics: null
    }
  },
  mounted() {
    // 初始化
    this.initializeChat()
  },
  methods: {
    async initializeChat() {
      try {
        const response = await fetch(`${this.apiBaseUrl}/init`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: this.sessionId,
            ...this.initParams
          })
        })
        
        const data = await response.json()
        if (data.status === 'success') {
          this.statistics = data.statistics
          // 添加欢迎消息
          if (this.messages.length === 0) {
            this.messages.push({
              role: 'ai',
              content: `欢迎使用向量数据库知识对话工具！共有 ${data.statistics.total_documents} 篇文档可供查询。`
            })
          }
        }
      } catch (error) {
        console.error('初始化失败:', error)
        this.messages.push({
          role: 'ai',
          content: '初始化失败，请稍后再试。' + error.message
        })
      }
    },
    
    async sendMessage() {
      const query = this.userInput.trim()
      if (!query || this.isLoading) return
      
      // 添加用户消息到聊天记录
      this.messages.push({
        role: 'user',
        content: query
      })
      
      this.userInput = ''
      this.isLoading = true
      
      try {
        // 准备发送的数据
        const data = {
          session_id: this.sessionId,
          query: query
        }
        
        // 如果设置了日期范围，添加到请求中
        if (this.startDate && this.endDate) {
          data.start_date = this.startDate
          data.end_date = this.endDate
        }
        
        // 发送请求到API
        const response = await fetch(`${this.apiBaseUrl}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(data)
        })
        
        const result = await response.json()
        if (result.status === 'success') {
          // 添加AI回复到聊天记录
          this.messages.push({
            role: 'ai',
            content: result.answer
          })
        } else {
          this.messages.push({
            role: 'ai',
            content: '抱歉，处理请求时出错。' + result.error
          })
        }
      } catch (error) {
        console.error('发送消息失败:', error)
        this.messages.push({
          role: 'ai',
          content: '抱歉，发送消息失败，请稍后再试。' + error.message
        })
      } finally {
        this.isLoading = false
        // 滚动到底部
        this.$nextTick(() => {
          const chatContainer = this.$el.querySelector('.chat-messages')
          if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight
          }
        })
      }
    },
    
    clearHistory() {
      // 清空本地消息
      this.messages = []
      // 调用API清空服务器端历史
      this.sendMessageToAPI('clear')
    },
    
    async getStatistics() {
      try {
        const response = await fetch(`${this.apiBaseUrl}/statistics`)
        const data = await response.json()
        if (data.status === 'success') {
          this.statistics = data.statistics
          this.messages.push({
            role: 'ai',
            content: `向量数据库统计信息：\n文档总数: ${data.statistics.total_documents}\n索引大小: ${(data.statistics.index_size / 1024).toFixed(2)} KB\n元数据大小: ${(data.statistics.metadata_size / 1024).toFixed(2)} KB`
          })
        }
      } catch (error) {
        console.error('获取统计信息失败:', error)
      }
    }
  }
}
</script>

<style scoped>
.vector-chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.vector-chat-container.embedded {
  height: 100%;
  border-radius: 0;
  box-shadow: none;
}

.chat-header {
  background-color: #4a6fa5;
  color: white;
  padding: 15px 20px;
  border-radius: 8px 8px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h2 {
  margin: 0;
  font-size: 18px;
}

.stats-info {
  font-size: 14px;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: white;
}

.message-wrapper {
  margin-bottom: 15px;
}

.message {
  display: flex;
  align-items: flex-start;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  margin: 0 10px;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background-color: #4a6fa5;
  color: white;
}

.message-content {
  flex: 1;
  padding: 10px 15px;
  border-radius: 18px;
  max-width: 70%;
}

.message.user .message-content {
  background-color: #4a6fa5;
  color: white;
}

.message.ai .message-content {
  background-color: #f0f0f0;
  color: #333;
}

.message-content p {
  margin: 0;
  line-height: 1.5;
}

.message-sources {
  margin-top: 8px;
  font-style: italic;
}

.loading-indicator {
  display: flex;
  align-items: center;
}

.loading-dot {
  width: 8px;
  height: 8px;
  background-color: #4a6fa5;
  border-radius: 50%;
  margin: 0 2px;
  animation: loading 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes loading {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.chat-input {
  padding: 15px 20px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
}

.date-filter {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
}

.date-filter input {
  padding: 5px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin: 0 5px;
}

.input-wrapper {
  display: flex;
  gap: 10px;
}

.input-wrapper input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 14px;
}

.input-wrapper button {
  padding: 10px 20px;
  background-color: #4a6fa5;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
}

.input-wrapper button:hover:not(:disabled) {
  background-color: #3a5a85;
}

.input-wrapper button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.chat-tips {
  margin-top: 10px;
  text-align: center;
}

.chat-tips small {
  color: #666;
  font-size: 12px;
}
</style>