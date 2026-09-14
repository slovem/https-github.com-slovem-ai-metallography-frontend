<template>
  <div class="user-audit-page">
    <a-page-header title="用户审核" sub-title="管理待审核的用户注册申请">
      <template #extra>
        <a-badge :count="pendingCount" :overflow-count="99">
          <a-button @click="loadPendingUsers">待审核</a-button>
        </a-badge>
      </template>
    </a-page-header>

    <!-- 待审核列表 -->
    <a-card title="待审核用户" style="margin-bottom: 16px;">
      <a-table
        :columns="pendingColumns"
        :data-source="pendingUsers"
        :loading="loading"
        row-key="id"
        :pagination="{ pageSize: 10 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'created_at'">
            {{ dayjs(record.created_at).format('YYYY-MM-DD HH:mm') }}
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="primary" size="small" @click="openAuditModal(record)">
                <CheckOutlined /> 审核
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
      <a-empty v-if="pendingUsers.length === 0 && !loading" description="暂无待审核用户" />
    </a-card>

    <!-- 所有用户列表 -->
    <a-card title="所有用户">
      <a-table
        :columns="allColumns"
        :data-source="allUsers"
        :loading="loading"
        row-key="id"
        :pagination="{ pageSize: 10 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'audit_status'">
            <a-tag :color="getStatusColor(record.audit_status)">
              {{ getStatusLabel(record.audit_status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'red'">
              {{ record.is_active ? '启用' : '停用' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'last_login'">
            {{ record.last_login ? dayjs(record.last_login).format('YYYY-MM-DD HH:mm') : '-' }}
          </template>
          <template v-if="column.key === 'created_at'">
            {{ dayjs(record.created_at).format('YYYY-MM-DD HH:mm') }}
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 审核弹窗 -->
    <a-modal
      v-model:open="showAuditModal"
      :title="`审核用户 - ${auditTarget?.username}`"
      @cancel="showAuditModal = false"
      :confirm-loading="auditing"
      :footer="null"
      width="500px"
    >
      <a-descriptions :column="1" bordered size="small">
        <a-descriptions-item label="用户名">{{ auditTarget?.username }}</a-descriptions-item>
        <a-descriptions-item label="邮箱">{{ auditTarget?.email }}</a-descriptions-item>
        <a-descriptions-item label="真实姓名">{{ auditTarget?.real_name || '-' }}</a-descriptions-item>
        <a-descriptions-item label="手机号">{{ auditTarget?.phone || '-' }}</a-descriptions-item>
        <a-descriptions-item label="部门">{{ auditTarget?.department || '-' }}</a-descriptions-item>
        <a-descriptions-item label="注册IP">{{ auditTarget?.register_ip || '-' }}</a-descriptions-item>
        <a-descriptions-item label="注册时间">{{ auditTarget?.created_at ? dayjs(auditTarget.created_at).format('YYYY-MM-DD HH:mm') : '-' }}</a-descriptions-item>
      </a-descriptions>

      <!-- 选择角色 -->
      <a-form-item label="分配角色" style="margin-top: 16px;">
        <a-select
          v-model:value="selectedRoleIds"
          mode="multiple"
          placeholder="请选择角色"
          style="width: 100%"
        >
          <a-select-option v-for="role in roles" :key="role.id" :value="role.id">
            {{ role.role_name }}
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="审核备注">
        <a-textarea v-model:value="auditRemark" placeholder="请输入审核备注（可选）" :rows="2" />
      </a-form-item>

      <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px;">
        <a-button @click="showAuditModal = false">取消</a-button>
        <a-button danger @click="confirmAudit('rejected')">
          <CloseOutlined /> 拒绝
        </a-button>
        <a-button type="primary" @click="confirmAudit('approved')">
          <CheckOutlined /> 通过
        </a-button>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { request } from '@/api/request'

interface User {
  id: number
  username: string
  email: string
  real_name: string
  phone: string
  department: string
  role: string
  audit_status: 'pending' | 'approved' | 'rejected'
  is_active: number
  last_login: string
  created_at: string
  register_ip: string
}

interface Role {
  id: number
  role_code: string
  role_name: string
  description: string
}

const loading = ref(false)
const auditing = ref(false)
const pendingUsers = ref<User[]>([])
const allUsers = ref<User[]>([])
const roles = ref<Role[]>([])
const showAuditModal = ref(false)
const auditTarget = ref<User | null>(null)
const auditRemark = ref('')
const selectedRoleIds = ref<number[]>([])

const pendingCount = computed(() => pendingUsers.value.length)

const pendingColumns = [
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  { title: '真实姓名', dataIndex: 'real_name', key: 'real_name' },
  { title: '手机号', dataIndex: 'phone', key: 'phone' },
  { title: '部门', dataIndex: 'department', key: 'department' },
  { title: '注册IP', dataIndex: 'register_ip', key: 'register_ip' },
  { title: '注册时间', key: 'created_at' },
  { title: '操作', key: 'action' }
]

const allColumns = [
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  { title: '真实姓名', dataIndex: 'real_name', key: 'real_name' },
  { title: '部门', dataIndex: 'department', key: 'department' },
  { title: '审核状态', key: 'audit_status' },
  { title: '状态', key: 'is_active' },
  { title: '上次登录', key: 'last_login' },
  { title: '注册时间', key: 'created_at' }
]

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    pending: 'orange',
    approved: 'green',
    rejected: 'red'
  }
  return map[status] || 'default'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return map[status] || status
}

// 加载角色列表
const loadRoles = async () => {
  try {
    const data = await request.get('/admin/roles')
    roles.value = data || []
  } catch (error) {
    console.error('加载角色失败:', error)
  }
}

// 加载待审核用户
const loadPendingUsers = async () => {
  loading.value = true
  try {
    const data = await request.get('/admin/users/pending')
    pendingUsers.value = data || []
  } catch (error: any) {
    message.error(error?.response?.data?.message || '加载待审核用户失败')
  } finally {
    loading.value = false
  }
}

// 加载所有用户
const loadAllUsers = async () => {
  loading.value = true
  try {
    const data = await request.get('/admin/users')
    allUsers.value = data || []
  } catch (error: any) {
    message.error(error?.response?.data?.message || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 打开审核弹窗
const openAuditModal = (user: User) => {
  auditTarget.value = user
  selectedRoleIds.value = []
  auditRemark.value = ''
  showAuditModal.value = true
}

// 确认审核
const confirmAudit = async (status: 'approved' | 'rejected') => {
  if (!auditTarget.value) return

  if (status === 'approved' && selectedRoleIds.value.length === 0) {
    message.warning('请至少选择一个角色')
    return
  }

  auditing.value = true
  try {
    await request.put(`/admin/users/${auditTarget.value.id}/audit`, {
      status: status,
      remark: auditRemark.value,
      roleIds: selectedRoleIds.value
    })
    message.success(`用户 ${auditTarget.value.username} 审核${status === 'approved' ? '通过' : '拒绝'}成功`)
    showAuditModal.value = false
    auditTarget.value = null
    auditRemark.value = ''
    selectedRoleIds.value = []
    await loadPendingUsers()
    await loadAllUsers()
  } catch (error: any) {
    message.error(error?.response?.data?.message || '审核失败')
  } finally {
    auditing.value = false
  }
}

onMounted(() => {
  loadRoles()
  loadPendingUsers()
  loadAllUsers()
})
</script>

<style scoped>
.user-audit-page {
  padding: 16px;
}
</style>