import type { Directive, App } from 'vue'
import { useAuthStore } from '@/stores/auth'

// 权限指令 - 用于控制元素显示
export const permissionDirective: Directive = {
  mounted(el: HTMLElement, binding) {
    const { value } = binding
    if (!value) return
    
    const authStore = useAuthStore()
    const permissionCodes = Array.isArray(value) ? value : [value]
    const hasPermission = permissionCodes.some(code => authStore.hasPermission(code))
    
    if (!hasPermission) {
      el.style.display = 'none'
    }
  }
}

// 注册指令
export function setupPermissionDirective(app: App) {
  app.directive('permission', permissionDirective)
}