<template>
  <div id="app">
    <VectorKnowledgeChat />
  </div>
</template>

<script>
import VectorKnowledgeChat from './VectorKnowledgeChat.vue'

export default {
  name: 'App',
  components: {
    VectorKnowledgeChat
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f5f5;
}

#app {
  height: 100vh;
  width: 100vw;
}
</style>