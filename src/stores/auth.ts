import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { request } from '@/api/request'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<any>(null)
  const permissions = ref<any[]>([])
  const permissionCodes = ref<string[]>([])
  const permissionVersion = ref<number>(0)

  const isLoggedIn = computed(() => !!token.value)

  const login = async (params: any) => {
    const response = await request.post('/auth/login', params)
    const { token: t, user } = response
    token.value = t
    userInfo.value = user
    localStorage.setItem('token', t)
    // 登录后立即从后端获取权限
    await fetchPermissions()
  }
const updatePermissions = (newPermissions: string[], newMenus: any[]) => {
  permissions.value = newPermissions
  menus.value = newMenus
  permissionVersion.value += 1
  
  localStorage.setItem('user_permissions', JSON.stringify(newPermissions))
  localStorage.setItem('user_menus', JSON.stringify(newMenus))
  localStorage.setItem('permission_version', String(permissionVersion.value))
}
  const fetchPermissions = async () => {
    try {
      console.log('🔄 从后端获取权限...')
      const data = await request.get('/auth/permissions')
      
      permissions.value = data.permissions || []
      permissionCodes.value = data.codes || []
      permissionVersion.value = data.version || 0
      
      // 只缓存到 localStorage，用于页面刷新时快速显示
      localStorage.setItem('user_permissions', JSON.stringify(permissions.value))
      localStorage.setItem('user_codes', JSON.stringify(permissionCodes.value))
      localStorage.setItem('permission_version', String(permissionVersion.value))
      
      console.log('✅ 权限加载成功，版本:', permissionVersion.value)
      console.log('✅ 权限列表:', permissionCodes.value)
      return true
    } catch (error) {
      console.error('❌ 获取权限失败:', error)
      permissions.value = []
      permissionCodes.value = []
      return false
    }
  }

  // 检查权限是否有更新（从后端检查版本号）
  const checkPermissionVersion = async (): Promise<boolean> => {
    try {
      // 只获取版本号，不获取完整权限
      const data = await request.get('/auth/permissions')
      const newVersion = data.version || 0
      
      if (newVersion > permissionVersion.value) {
        console.log('🔄 检测到权限版本变化，重新加载...')
        permissions.value = data.permissions || []
        permissionCodes.value = data.codes || []
        permissionVersion.value = newVersion
        localStorage.setItem('user_permissions', JSON.stringify(permissions.value))
        localStorage.setItem('user_codes', JSON.stringify(permissionCodes.value))
        localStorage.setItem('permission_version', String(newVersion))
        return true
      }
      return false
    } catch (error) {
      console.error('检查权限版本失败:', error)
      return false
    }
  }

  // 只用于页面刷新时的快速显示，不依赖缓存数据
  const restorePermissions = () => {
    try {
      const saved = localStorage.getItem('user_permissions')
      const codes = localStorage.getItem('user_codes')
      const version = localStorage.getItem('permission_version')
      
      if (saved) {
        permissions.value = JSON.parse(saved)
        console.log('🔄 从缓存恢复权限（快速显示），版本:', version)
      }
      if (codes) {
        permissionCodes.value = JSON.parse(codes)
      }
      if (version) {
        permissionVersion.value = parseInt(version)
      }
      
      // 注意：这里只是快速显示，真正的权限以后端为准
      // 在路由守卫中会再次从后端获取
    } catch (error) {
      console.error('恢复权限失败:', error)
    }
  }

  const hasPermission = (code: string): boolean => {
    return permissionCodes.value.includes(code)
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    permissions.value = []
    permissionCodes.value = []
    permissionVersion.value = 0
    localStorage.removeItem('token')
    localStorage.removeItem('user_permissions')
    localStorage.removeItem('user_codes')
    localStorage.removeItem('permission_version')
  }

  // 构建菜单树
  const menuTree = computed(() => {
    const all = permissions.value
    if (all.length === 0) return []
    const top = all.filter((p: any) => p.parent_id === 0 && p.is_menu === 1)
    return top.map((menu: any) => {
      const children = all.filter((p: any) => p.parent_id === menu.id && p.is_menu === 1)
      return {
        key: menu.path || `/${menu.permission_code}`,
        label: menu.permission_name,
        icon: menu.icon || 'FileOutlined',
        path: menu.path || `/${menu.permission_code}`,
        children: children.map((child: any) => ({
          key: child.path || `/${child.permission_code}`,
          label: child.permission_name,
          path: child.path || `/${child.permission_code}`
        }))
      }
    })
  })

  return {
    token,
    userInfo,
    permissions,
    permissionCodes,
    permissionVersion,
    menuTree,
    isLoggedIn,
    login,
    fetchPermissions,
    checkPermissionVersion,
    hasPermission,
    logout,
    restorePermissions
  }
})