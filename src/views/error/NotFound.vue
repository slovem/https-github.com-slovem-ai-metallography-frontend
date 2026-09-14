<template>
  <div class="not-found">
    <a-result status="404" title="404" sub-title="页面未找到">
      <template #extra>
        <a-button type="primary" @click="$router.push('/dashboard')">
          返回首页
        </a-button>
      </template>
    </a-result>
  </div>
</template>