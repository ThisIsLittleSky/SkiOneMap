<template>
  <div ref="containerEl" class="ski-scene"></div>

  <!-- 摄像头点击弹窗 -->
  <Teleport to="body">
    <Transition name="popup">
      <div v-if="activeCamera" class="cam-popup" :style="popupStyle">
        <div class="cam-popup-header">
          <span class="cam-icon">📷</span>
          <span class="cam-name">{{ activeCamera.name }}</span>
          <button class="cam-close" @click="activeCamera = null">×</button>
        </div>
        <div class="cam-popup-body">
          <div class="cam-row">
            <span class="label">状态</span>
            <span :class="activeCamera.status === 'ONLINE' ? 'online' : 'offline'">
              {{ activeCamera.status === 'ONLINE' ? '● 在线' : '○ 离线' }}
            </span>
          </div>
          <div class="cam-row">
            <span class="label">位置</span>
            <span>X:{{ activeCamera.posX }} Y:{{ activeCamera.posY }} Z:{{ activeCamera.posZ }}</span>
          </div>
          <div v-if="activeCamera.description" class="cam-row">
            <span class="label">描述</span>
            <span>{{ activeCamera.description }}</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import type { CameraInfo } from '@/api'

const props = defineProps<{ cameras: CameraInfo[]; selectedCameraId?: number | null }>()

const containerEl = ref<HTMLElement>()
let renderer: THREE.WebGLRenderer
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let controls: OrbitControls
let animId: number
let camMeshes: { mesh: THREE.Object3D; data: CameraInfo }[] = []
const raycaster = new THREE.Raycaster()
const mouse = new THREE.Vector2()

const activeCamera = ref<CameraInfo | null>(null)
const popupStyle = ref({ left: '0px', top: '0px' })

function init() {
  const el = containerEl.value!
  const w = el.clientWidth, h = el.clientHeight

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(w, h)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 2.0
  el.appendChild(renderer.domElement)

  // Scene
  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x0a1929, 0.008)

  // Camera
  camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 2000)
  camera.position.set(0, 80, 150)

  // Lights
  const ambient = new THREE.AmbientLight(0xb0c4de, 0.9)
  scene.add(ambient)
  const sun = new THREE.DirectionalLight(0xfff5e0, 1.4)
  sun.position.set(80, 120, 60)
  sun.castShadow = true
  scene.add(sun)
  const fill = new THREE.DirectionalLight(0x8ab4f8, 1.0)
  fill.position.set(-60, 40, -80)
  scene.add(fill)

  // OrbitControls
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.minDistance = 20
  controls.maxDistance = 400
  controls.maxPolarAngle = Math.PI / 2.1

  // 加载 GLB 模型
  const loader = new GLTFLoader()
  loader.load(
    '/7秒换视角.glb',
    (gltf) => {
      const model = gltf.scene
      // 自动居中缩放
      const box = new THREE.Box3().setFromObject(model)
      const center = box.getCenter(new THREE.Vector3())
      const size = box.getSize(new THREE.Vector3())
      const maxDim = Math.max(size.x, size.y, size.z)
      const scale = 100 / maxDim
      model.scale.setScalar(scale)
      model.position.sub(center.multiplyScalar(scale))
      model.position.y += size.y * scale * 0.3
      model.traverse(child => {
        if ((child as THREE.Mesh).isMesh) {
          child.castShadow = true
          child.receiveShadow = true
        }
      })
      scene.add(model)
    },
    undefined,
    (err) => console.error('GLB load error:', err)
  )

  // 地面网格（雪地感）
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(400, 400),
    new THREE.MeshStandardMaterial({ color: 0xd0e8f8, roughness: 0.9, metalness: 0 })
  )
  ground.rotation.x = -Math.PI / 2
  ground.position.y = -0.5
  ground.receiveShadow = true
  scene.add(ground)

  // 构建摄像头标注
  buildCameraMeshes()

  // 雪花粒子系统
  buildSnowParticles()

  // Click 事件
  renderer.domElement.addEventListener('click', onSceneClick)

  // Resize
  window.addEventListener('resize', onResize)

  animate()
}

function buildCameraMeshes() {
  // 清除旧的
  camMeshes.forEach(({ mesh }) => scene.remove(mesh))
  camMeshes = []

  props.cameras.forEach(cam => {
    const group = new THREE.Group()

    // 圆锥本体
    const cone = new THREE.Mesh(
      new THREE.ConeGeometry(1.2, 3, 8),
      new THREE.MeshStandardMaterial({
        color: cam.status === 'ONLINE' ? 0x00e5ff : 0x607d8b,
        emissive: cam.status === 'ONLINE' ? 0x00bcd4 : 0x37474f,
        emissiveIntensity: 0.6,
      })
    )
    cone.rotation.x = Math.PI  // 尖朝下
    cone.position.y = 1.5

    // 光晕圆环
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(1.8, 0.15, 8, 32),
      new THREE.MeshStandardMaterial({
        color: cam.status === 'ONLINE' ? 0x00e5ff : 0x607d8b,
        emissive: cam.status === 'ONLINE' ? 0x00e5ff : 0x546e7a,
        emissiveIntensity: 1,
        transparent: true,
        opacity: 0.7,
      })
    )
    ring.rotation.x = Math.PI / 2
    ring.position.y = 3.5

    // 竖直杆
    const pole = new THREE.Mesh(
      new THREE.CylinderGeometry(0.15, 0.15, 4, 6),
      new THREE.MeshStandardMaterial({ color: 0x546e7a })
    )
    pole.position.y = 2

    group.add(cone, ring, pole)
    group.position.set(cam.posX, cam.posY, cam.posZ)
    group.userData = { cameraData: cam }
    scene.add(group)
    camMeshes.push({ mesh: group, data: cam })
  })
}

let snowParticles: THREE.Points | null = null
let snowPositions: Float32Array | null = null
const SNOW_COUNT = 1200

function buildSnowParticles() {
  const geometry = new THREE.BufferGeometry()
  const positions = new Float32Array(SNOW_COUNT * 3)
  for (let i = 0; i < SNOW_COUNT; i++) {
    positions[i * 3]     = (Math.random() - 0.5) * 300
    positions[i * 3 + 1] = Math.random() * 160
    positions[i * 3 + 2] = (Math.random() - 0.5) * 300
  }
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  snowPositions = positions

  const material = new THREE.PointsMaterial({
    color: 0xd0e8ff,
    size: 0.55,
    transparent: true,
    opacity: 0.7,
    sizeAttenuation: true,
  })
  snowParticles = new THREE.Points(geometry, material)
  scene.add(snowParticles)
}

function onSceneClick(e: MouseEvent) {
  const el = containerEl.value!
  const rect = el.getBoundingClientRect()
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)
  const targets = camMeshes.map(c => c.mesh)
  const hits = raycaster.intersectObjects(targets, true)
  if (hits.length > 0) {
    let obj: THREE.Object3D | null = hits[0].object
    while (obj && !obj.userData.cameraData) obj = obj.parent
    if (obj?.userData.cameraData) {
      activeCamera.value = obj.userData.cameraData
      popupStyle.value = { left: `${e.clientX + 12}px`, top: `${e.clientY - 20}px` }
    }
  } else {
    activeCamera.value = null
  }
}

function onResize() {
  const el = containerEl.value!
  const w = el.clientWidth, h = el.clientHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
}

function animate() {
  animId = requestAnimationFrame(animate)
  // 光晕脉冲动画
  const t = Date.now() * 0.002
  camMeshes.forEach(({ mesh }) => {
    const ring = mesh.children[1] as THREE.Mesh
    if (ring?.material) {
      const mat = ring.material as THREE.MeshStandardMaterial
      mat.opacity = 0.4 + Math.sin(t + mesh.position.x) * 0.3
    }
  })
  // 雪花下落动画
  if (snowPositions && snowParticles) {
    for (let i = 0; i < SNOW_COUNT; i++) {
      snowPositions[i * 3 + 1] -= 0.12 + (i % 5) * 0.03
      snowPositions[i * 3]     += Math.sin(t * 0.5 + i) * 0.04
      if (snowPositions[i * 3 + 1] < -2) {
        snowPositions[i * 3 + 1] = 160
      }
    }
    snowParticles.geometry.attributes.position.needsUpdate = true
  }
  controls.update()
  renderer.render(scene, camera)
}

onMounted(init)

onUnmounted(() => {
  cancelAnimationFrame(animId)
  window.removeEventListener('resize', onResize)
  renderer?.domElement.removeEventListener('click', onSceneClick)
  snowParticles?.geometry.dispose()
  renderer?.dispose()
})

watch(() => props.cameras, buildCameraMeshes, { deep: true })

watch(() => props.selectedCameraId, (id) => {
  if (id == null) {
    activeCamera.value = null
    return
  }
  const found = camMeshes.find(c => c.data.id === id)
  if (!found) return
  activeCamera.value = found.data
  // 将摄像头位置投影到屏幕中心附近显示弹窗
  const el = containerEl.value!
  const rect = el.getBoundingClientRect()
  const pos = found.mesh.position.clone()
  pos.project(camera)
  const x = (pos.x * 0.5 + 0.5) * rect.width + rect.left
  const y = (-pos.y * 0.5 + 0.5) * rect.height + rect.top
  popupStyle.value = { left: `${x + 12}px`, top: `${y - 20}px` }
})
</script>

<style scoped>
.ski-scene {
  width: 100%;
  height: 100%;
  cursor: grab;
}
.ski-scene:active { cursor: grabbing; }

.cam-popup {
  position: fixed;
  z-index: 2000;
  background: rgba(10, 25, 41, 0.95);
  border: 1px solid #00e5ff44;
  border-radius: 8px;
  width: 220px;
  box-shadow: 0 0 20px rgba(0, 229, 255, 0.2);
  backdrop-filter: blur(8px);
}

.cam-popup-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid #1e3a5f;
}

.cam-icon { font-size: 16px; }
.cam-name { flex: 1; font-size: 13px; font-weight: 600; color: #00e5ff; }
.cam-close { background: none; border: none; color: #546e7a; font-size: 18px; cursor: pointer; line-height: 1; }
.cam-close:hover { color: #fff; }

.cam-popup-body { padding: 10px 12px; display: flex; flex-direction: column; gap: 6px; }
.cam-row { display: flex; gap: 8px; font-size: 12px; color: #cfd8dc; }
.label { color: #90a4ae; width: 36px; flex-shrink: 0; }
.online { color: #00e5ff; }
.offline { color: #90a4ae; }

.popup-enter-active, .popup-leave-active { transition: opacity 0.15s, transform 0.15s; }
.popup-enter-from, .popup-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
