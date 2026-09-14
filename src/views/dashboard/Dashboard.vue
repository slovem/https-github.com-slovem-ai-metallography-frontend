<template>
  <div class="dashboard">
    <h2>📊 数据看板</h2>
    <p style="color: #888; margin-top: 20px;">AI金相识别系统已就绪 ✅</p>
    <div style="margin-top: 30px; display: flex; gap: 20px; justify-content: center;">
      <a-card style="width: 200px;">
        <a-statistic title="总检测任务" :value="1258" />
      </a-card>
      <a-card style="width: 200px;">
        <a-statistic title="今日新增" :value="23" />
      </a-card>
      <a-card style="width: 200px;">
        <a-statistic title="待检测" :value="12" />
      </a-card>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 40px;
  text-align: center;
}
</style>