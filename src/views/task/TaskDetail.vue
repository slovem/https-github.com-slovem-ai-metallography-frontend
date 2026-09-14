<template>
  <div class="task-detail">
    <a-page-header
      title="任务详情"
      sub-title="查看检测任务完整信息"
      @back="$router.back()"
    >
      <template #extra>
        <a-space>
          <a-tag color="green">已完成</a-tag>
          <a-button type="primary">
            <FilePdfOutlined /> 导出报告
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-card title="基本信息" style="margin-top: 16px;">
      <a-descriptions :column="3" bordered>
        <a-descriptions-item label="任务编号">T20260618001</a-descriptions-item>
        <a-descriptions-item label="材料牌号">45#钢</a-descriptions-item>
        <a-descriptions-item label="检测标准">GB/T 6394 晶粒度</a-descriptions-item>
        <a-descriptions-item label="热处理状态">淬火+回火</a-descriptions-item>
        <a-descriptions-item label="图片数量">5 张</a-descriptions-item>
        <a-descriptions-item label="创建时间">2026-06-18 08:00</a-descriptions-item>
      </a-descriptions>
    </a-card>

    <a-card title="检测结果" style="margin-top: 16px;">
      <a-empty description="识别结果展示开发中..." />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
const taskId = route.params.id
console.log('任务ID:', taskId)
</script>

<style scoped>
.task-detail {
  padding: 16px;
}
</style>