<template>
  <a-layout class="default-layout">
    <!-- 侧边栏 -->
    <a-layout-sider v-model:collapsed="collapsed" :trigger="null" collapsible class="sidebar" theme="dark">
      <div class="logo">
        <span class="logo-icon">🔬</span>
        <span v-if="!collapsed" class="logo-text">AI金相识别</span>
      </div>
      <a-menu theme="dark" mode="inline" v-model:selectedKeys="selectedKeys" v-model:openKeys="openKeys" @click="handleMenuClick">
        <template v-for="menu in menuItems" :key="menu.key">
          <a-sub-menu v-if="menu.children && menu.children.length > 0" :key="menu.key">
            <template #title>
              <component :is="menu.icon || 'FileOutlined'" />
              <span>{{ menu.label }}</span>
            </template>
            <a-menu-item v-for="child in menu.children" :key="child.key">
              {{ child.label }}
            </a-menu-item>
          </a-sub-menu>
          <a-menu-item v-else :key="menu.key">
            <component :is="menu.icon || 'FileOutlined'" />
            <span>{{ menu.label }}</span>
          </a-menu-item>
        </template>
      </a-menu>
    </a-layout-sider>

    <!-- 主内容区 -->
    <a-layout>
      <!-- 顶部导航 -->
      <a-layout-header class="header">
        <div class="header-left">
          <MenuUnfoldOutlined v-if="collapsed" class="trigger" @click="collapsed = !collapsed" />
          <MenuFoldOutlined v-else class="trigger" @click="collapsed = !collapsed" />
          <a-breadcrumb class="breadcrumb">
            <a-breadcrumb-item>{{ route.meta?.title || '首页' }}</a-breadcrumb-item>
          </a-breadcrumb>
        </div>
        <div class="header-right">
          <a-dropdown>
            <div class="user-info">
              <a-avatar size="small" style="backgroundColor: #667eea">{{ userInitial }}</a-avatar>
              <span class="username">{{ username }}</span>
            </div>
            <template #overlay>
              <a-menu>
                <a-menu-item key="logout" @click="handleLogout">
                  <LogoutOutlined /> 退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 内容区 -->
      <a-layout-content class="content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>(['/dashboard'])
const openKeys = ref<string[]>([])

let checkInterval: ReturnType<typeof setInterval> | null = null

const username = computed(() => authStore.userInfo?.fullName || authStore.userInfo?.username || '用户')
const userInitial = computed(() => username.value.charAt(0))

// 菜单树
const menuItems = computed(() => authStore.menuTree)

const handleMenuClick = ({ key }: { key: string }) => {
  if (key === '/system') {
    router.push('/system/roles')
    return
  }
  router.push(key)
}

const handleLogout = () => {
  authStore.logout()
  message.success('已退出登录')
  router.push('/auth/login')
}

watch(() => route.path, (path) => {
  selectedKeys.value = [path]
})

// 定期检查权限是否更新（每10秒）
const startCheckPermission = () => {
  if (checkInterval) return
  checkInterval = setInterval(async () => {
    if (authStore.isLoggedIn) {
      const hasUpdate = await authStore.checkPermissionVersion()
      if (hasUpdate) {
        message.info('权限已更新，页面即将刷新...')
        setTimeout(() => {
          window.location.reload()
        }, 1000)
      }
    }
  }, 10000)
}

const checkPermissionOnVisible = async () => {
  if (document.visibilityState === 'visible' && authStore.isLoggedIn) {
    const hasUpdate = await authStore.checkPermissionVersion()
    if (hasUpdate) {
      message.info('权限已更新，页面即将刷新...')
      setTimeout(() => {
        window.location.reload()
      }, 1000)
    }
  }
}

onMounted(async () => {
  if (authStore.isLoggedIn) {
    await authStore.fetchPermissions()
  }
  selectedKeys.value = [route.path]
  
  startCheckPermission()
  document.addEventListener('visibilitychange', checkPermissionOnVisible)
  
  console.log('📋 菜单已加载')
})

onUnmounted(() => {
  if (checkInterval) {
    clearInterval(checkInterval)
    checkInterval = null
  }
  document.removeEventListener('visibilitychange', checkPermissionOnVisible)
})
</script>

<style scoped lang="scss">
.default-layout {
  min-height: 100vh;
  
  .sidebar {
    .logo {
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 16px;
      .logo-icon { font-size: 28px; }
      .logo-text { color: #fff; font-size: 18px; font-weight: 700; margin-left: 10px; white-space: nowrap; }
    }
  }
  
  .header {
    background: #fff;
    padding: 0 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    z-index: 1;
    
    .header-left {
      display: flex;
      align-items: center;
      .trigger { font-size: 18px; cursor: pointer; transition: color 0.3s; &:hover { color: #667eea; } }
      .breadcrumb { margin-left: 16px; }
    }
    
    .header-right {
      .user-info {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        .username { font-size: 14px; }
      }
    }
  }
  
  .content {
    margin: 24px;
    padding: 24px;
    background: #fff;
    border-radius: 8px;
    min-height: 280px;
  }
}
</style>