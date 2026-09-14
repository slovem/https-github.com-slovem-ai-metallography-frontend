<template>
  <div class="task-list">
    <h2>检测任务</h2>
    <a-button type="primary" @click="$router.push('/tasks/create')">
      <PlusOutlined /> 新建任务
    </a-button>
    <a-table :columns="columns" :data-source="[]" style="margin-top: 16px;">
      <template #empty>
        <a-empty description="暂无检测任务" />
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
const columns = [
  { title: '任务编号', dataIndex: 'code', key: 'code' },
  { title: '材料牌号', dataIndex: 'material', key: 'material' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt' },
  { title: '操作', key: 'action' }
]
</script>