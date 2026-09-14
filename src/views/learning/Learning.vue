<template>
  <div class="learning-page">
    <a-page-header title="模型学习" sub-title="AI模型训练与管理平台">
      <template #extra>
        <a-button type="primary" @click="handleNewTraining">
          <PlusOutlined /> 新建训练
        </a-button>
      </template>
    </a-page-header>

    <a-row :gutter="16">
      <a-col :span="6">
        <a-card>
          <a-statistic title="训练次数" :value="42" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="模型版本" :value="8" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="平均准确率" :value="92.5" suffix="%" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="待标注数据" :value="156" />
        </a-card>
      </a-col>
    </a-row>

    <a-card title="训练任务列表" style="margin-top: 16px;">
      <a-table :columns="columns" :data-source="trainingData" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusLabel(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'accuracy'">
            <a-progress :percent="record.accuracy" size="small" />
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { message } from 'ant-design-vue'

const columns = [
  { title: '任务编号', dataIndex: 'id', key: 'id' },
  { title: '模型名称', dataIndex: 'modelName', key: 'modelName' },
  { title: '数据集', dataIndex: 'dataset', key: 'dataset' },
  { title: '状态', key: 'status' },
  { title: '准确率', key: 'accuracy' },
  { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt' }
]

const trainingData = ref([
  { id: 'T001', modelName: 'YOLOv8-钢铁-晶粒度', dataset: '晶粒度数据集 v2.0', status: 'completed', accuracy: 94.5, createdAt: '2026-06-18 10:00' },
  { id: 'T002', modelName: 'YOLOv8-钢铁-夹杂物', dataset: '夹杂物数据集 v1.5', status: 'training', accuracy: 87.2, createdAt: '2026-06-18 09:00' },
  { id: 'T003', modelName: 'YOLOv8-钢铁-综合', dataset: '综合数据集 v3.0', status: 'pending', accuracy: 0, createdAt: '2026-06-17 16:30' }
])

const getStatusColor = (status: string) => {
  const map: Record<string, string> = { pending: 'orange', training: 'blue', completed: 'green', failed: 'red' }
  return map[status] || 'default'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = { pending: '等待中', training: '训练中', completed: '已完成', failed: '失败' }
  return map[status] || status
}

const handleNewTraining = () => {
  message.info('新建训练任务功能开发中...')
}
</script>

<style scoped>
.learning-page {
  padding: 16px;
}
</style>