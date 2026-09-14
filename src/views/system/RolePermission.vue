<template>
  <div class="role-permission-page">
    <a-page-header title="角色权限管理" sub-title="配置不同角色的功能权限">
      <template #extra>
        <a-button type="primary" @click="handleAddRole">
          <PlusOutlined /> 新增角色
        </a-button>
      </template>
    </a-page-header>

    <a-row :gutter="16">
      <!-- 左侧：角色列表 -->
      <a-col :span="6">
        <a-card title="角色列表" :bordered="false">
          <a-spin :spinning="loading">
            <a-list :data-source="roles" size="small">
              <template #renderItem="{ item }">
                <a-list-item
                  :class="{ 'active-item': selectedRole?.id === item.id }"
                  @click="selectRole(item)"
                  style="cursor: pointer;"
                >
                  <a-list-item-meta>
                    <template #title>
                      <a-space>
                        <span>{{ item.role_name }}</span>
                        <a-tag size="small" :color="item.is_active ? 'green' : 'red'">
                          {{ item.is_active ? '启用' : '停用' }}
                        </a-tag>
                      </a-space>
                    </template>
                    <template #description>
                      <span style="font-size: 12px; color: #999;">{{ item.description || '暂无描述' }}</span>
                    </template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </a-spin>
        </a-card>
      </a-col>

      <!-- 右侧：权限配置 -->
      <a-col :span="18">
        <a-card :title="selectedRole ? `配置权限 - ${selectedRole.role_name}` : '请选择角色'" :bordered="false">
          <template v-if="selectedRole">
            <a-spin :spinning="permissionLoading">
              <a-row :gutter="[16, 16]">
                <!-- 遍历顶级权限 -->
                <a-col :span="12" v-for="menu in menuList" :key="menu.id">
                  <a-card size="small" :title="menu.permission_name" :bordered="true">
                    <!-- 每个菜单独立使用 v-model -->
                    <a-checkbox-group v-model:value="menuSelectedMap[menu.id]">
                      <a-row>
                        <!-- 菜单本身的权限 -->
                        <a-col :span="24" v-if="menu.is_menu === 1">
                          <a-checkbox :value="menu.id">
                            {{ menu.permission_name }}
                          </a-checkbox>
                        </a-col>
                        <!-- 子权限 -->
                        <a-col :span="24" v-for="child in getChildren(menu.id)" :key="child.id">
                          <a-checkbox :value="child.id">
                            {{ child.permission_name }}
                          </a-checkbox>
                        </a-col>
                      </a-row>
                    </a-checkbox-group>
                  </a-card>
                </a-col>
              </a-row>
            </a-spin>

            <div style="margin-top: 16px; text-align: right;">
              <a-space>
                <a-button @click="resetPermissions">重置</a-button>
                <a-button type="primary" :loading="saving" @click="savePermissions">
                  保存配置
                </a-button>
              </a-space>
            </div>
          </template>
          <a-empty v-else description="请从左侧选择一个角色" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 新增角色弹窗 -->
    <a-modal
      v-model:open="showAddModal"
      title="新增角色"
      @ok="handleAddRoleSubmit"
      @cancel="showAddModal = false"
      :confirm-loading="addLoading"
    >
      <a-form :model="newRole" layout="vertical">
        <a-form-item label="角色编码" required>
          <a-input v-model:value="newRole.role_code" placeholder="如：manager" />
        </a-form-item>
        <a-form-item label="角色名称" required>
          <a-input v-model:value="newRole.role_name" placeholder="如：部门经理" />
        </a-form-item>
        <a-form-item label="角色描述">
          <a-textarea v-model:value="newRole.description" placeholder="角色描述" :rows="2" />
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="newRole.is_active" checked-children="启用" un-checked-children="停用" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import { request } from '@/api/request'
import { useAuthStore } from '@/stores/auth'

interface Role {
  id: number
  role_code: string
  role_name: string
  description: string
  is_active: number
}

interface Permission {
  id: number
  parent_id: number
  permission_code: string
  permission_name: string
  path: string
  icon: string
  is_menu: number
  sort_order: number
}

const loading = ref(false)
const permissionLoading = ref(false)
const saving = ref(false)
const addLoading = ref(false)
const showAddModal = ref(false)

const roles = ref<Role[]>([])
const allPermissions = ref<Permission[]>([])
const selectedRole = ref<Role | null>(null)

// 每个菜单独立存储选中的权限ID
const menuSelectedMap = reactive<Record<number, number[]>>({})

// 计算所有选中的权限ID（用于提交保存）
const selectedPermissionIds = computed(() => {
  const allIds: number[] = []
  Object.values(menuSelectedMap).forEach(ids => {
    allIds.push(...ids)
  })
  return allIds
})

const newRole = ref({
  role_code: '',
  role_name: '',
  description: '',
  is_active: true
})

// 获取所有顶级菜单
const menuList = computed(() => {
  return allPermissions.value.filter(p => p.parent_id === 0)
})

// 获取某个菜单下的子权限
const getChildren = (parentId: number) => {
  return allPermissions.value.filter(p => p.parent_id === parentId)
}

// 加载角色列表
const loadRoles = async () => {
  loading.value = true
  try {
    const data = await request.get('/admin/roles')
    roles.value = data || []
  } catch (error: any) {
    console.error('加载角色列表失败:', error)
    message.error(error?.response?.data?.message || '加载角色列表失败')
  } finally {
    loading.value = false
  }
}

// 加载所有权限
const loadPermissions = async () => {
  permissionLoading.value = true
  try {
    const data = await request.get('/admin/permissions')
    allPermissions.value = data || []
    console.log('✅ 权限数据:', allPermissions.value)
  } catch (error: any) {
    console.error('加载权限列表失败:', error)
    message.error(error?.response?.data?.message || '加载权限列表失败')
  } finally {
    permissionLoading.value = false
  }
}

// 加载角色的权限
const loadRolePermissions = async (roleId: number) => {
  try {
    const data = await request.get(`/admin/roles/${roleId}/permissions`)
    const permissionIds = data || []
    console.log('✅ 角色权限ID:', permissionIds)
    
    // 按菜单分组填充选中状态
    // 先清空所有菜单的选中状态
    Object.keys(menuSelectedMap).forEach(key => {
      delete menuSelectedMap[key]
    })
    
    // 按父级分组
    allPermissions.value.forEach(p => {
      if (permissionIds.includes(p.id)) {
        const parentId = p.parent_id || p.id
        if (!menuSelectedMap[parentId]) {
          menuSelectedMap[parentId] = []
        }
        if (!menuSelectedMap[parentId].includes(p.id)) {
          menuSelectedMap[parentId].push(p.id)
        }
      }
    })
    
    console.log('✅ 按菜单分组的权限:', menuSelectedMap)
  } catch (error: any) {
    console.error('加载角色权限失败:', error)
    message.error(error?.response?.data?.message || '加载角色权限失败')
  }
}

// 选择角色
const selectRole = (role: Role) => {
  selectedRole.value = role
  loadRolePermissions(role.id)
}

// 保存权限
const savePermissions = async () => {
  if (!selectedRole.value) return
  
  saving.value = true
  try {
    await request.put(`/admin/roles/${selectedRole.value.id}/permissions`, {
      permissionIds: selectedPermissionIds.value
    })
    message.success('权限配置保存成功')
    
    const authStore = useAuthStore()
    if (authStore.userInfo?.id === selectedRole.value.id) {
      // 重新获取完整权限数据
      const permData = await request.get('/auth/permissions')
      authStore.updatePermissions(permData.permissions, permData.menus)
      message.success('权限已立即生效')
    } else {
      message.info('权限已更新，该用户下次操作时将自动生效')
    }
  } catch (error: any) {
    console.error('保存失败:', error)
    message.error(error?.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// 重置权限
const resetPermissions = () => {
  if (selectedRole.value) {
    loadRolePermissions(selectedRole.value.id)
    message.info('已重置')
  }
}

// 新增角色
const handleAddRole = () => {
  newRole.value = {
    role_code: '',
    role_name: '',
    description: '',
    is_active: true
  }
  showAddModal.value = true
}

// 提交新增角色
const handleAddRoleSubmit = async () => {
  if (!newRole.value.role_code || !newRole.value.role_name) {
    message.warning('请填写角色编码和名称')
    return
  }
  
  addLoading.value = true
  try {
    await request.post('/admin/roles', {
      ...newRole.value,
      is_active: newRole.value.is_active ? 1 : 0
    })
    message.success('角色创建成功')
    showAddModal.value = false
    loadRoles()
  } catch (error: any) {
    console.error('创建角色失败:', error)
    message.error(error?.response?.data?.message || '创建失败')
  } finally {
    addLoading.value = false
  }
}

onMounted(() => {
  loadRoles()
  loadPermissions()
})
</script>

<style scoped>
.role-permission-page {
  padding: 16px;
}

.active-item {
  background-color: #e6f7ff;
  border-left: 3px solid #1890ff;
}

:deep(.ant-list-item) {
  padding: 12px 16px;
  transition: all 0.3s;
}

:deep(.ant-list-item:hover) {
  background-color: #f5f5f5;
}
</style>