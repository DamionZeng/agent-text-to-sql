<template>
  <div
    class="shape"
    :class="{ active }"
    :style="shapeStyle"
    @mousedown.stop="handleMouseDown"
  >
    <!-- Resize Handles -->
    <div
      v-if="active"
      v-for="point in pointList"
      :key="point"
      class="shape-point"
      :style="getPointStyle(point)"
      @mousedown.stop="handleResize($event, point)"
    ></div>

    <slot></slot>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  active: Boolean,
  defaultStyle: Object,
  scale: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['update:style', 'mousedown'])

const pointList = ['t', 'r', 'b', 'l', 'lt', 'rt', 'lb', 'rb']

const shapeStyle = computed(() => {
  return {
    left: `${props.defaultStyle.x}px`,
    top: `${props.defaultStyle.y}px`,
    width: `${props.defaultStyle.w}px`,
    height: `${props.defaultStyle.h}px`,
    zIndex: props.defaultStyle.z
  }
})

const getPointStyle = (point) => {
  const { w, h } = props.defaultStyle
  const hasT = /t/.test(point)
  const hasB = /b/.test(point)
  const hasL = /l/.test(point)
  const hasR = /r/.test(point)
  let newLeft = 0
  let newTop = 0

  if (point.length === 2) {
    newLeft = hasL ? 0 : w
    newTop = hasT ? 0 : h
  } else {
    if (hasT || hasB) {
      newLeft = w / 2
      newTop = hasT ? 0 : h
    }
    if (hasL || hasR) {
      newLeft = hasL ? 0 : w
      newTop = h / 2
    }
  }

  const style = {
    marginLeft: '-4px',
    marginTop: '-4px',
    left: `${newLeft}px`,
    top: `${newTop}px`,
    cursor: getCursorStyle(point)
  }
  return style
}

const getCursorStyle = (point) => {
  const map = {
    t: 'ns-resize',
    b: 'ns-resize',
    l: 'ew-resize',
    r: 'ew-resize',
    lt: 'nwse-resize',
    rb: 'nwse-resize',
    rt: 'nesw-resize',
    lb: 'nesw-resize'
  }
  return map[point]
}

const handleMouseDown = (e) => {
  emit('mousedown', e)
  
  const startY = e.clientY
  const startX = e.clientX
  const startTop = props.defaultStyle.y
  const startLeft = props.defaultStyle.x

  const move = (moveEvent) => {
    const currX = moveEvent.clientX
    const currY = moveEvent.clientY
    emit('update:style', {
      ...props.defaultStyle,
      y: Math.round(startTop + (currY - startY) / props.scale),
      x: Math.round(startLeft + (currX - startX) / props.scale)
    })
  }

  const up = () => {
    document.removeEventListener('mousemove', move)
    document.removeEventListener('mouseup', up)
  }

  document.addEventListener('mousemove', move)
  document.addEventListener('mouseup', up)
}

const handleResize = (e, point) => {
  const startX = e.clientX
  const startY = e.clientY
  const { x, y, w, h } = props.defaultStyle
  const { scale } = props

  const move = (moveEvent) => {
    const currX = moveEvent.clientX
    const currY = moveEvent.clientY
    const disY = (currY - startY) / scale
    const disX = (currX - startX) / scale

    const hasT = /t/.test(point)
    const hasB = /b/.test(point)
    const hasL = /l/.test(point)
    const hasR = /r/.test(point)

    let newHeight = h + (hasT ? -disY : hasB ? disY : 0)
    let newWidth = w + (hasL ? -disX : hasR ? disX : 0)
    let newTop = y + (hasT ? disY : 0)
    let newLeft = x + (hasL ? disX : 0)

    // Minimum size
    if (newWidth < 20) {
      newWidth = 20
      newLeft = x + (hasL ? w - 20 : 0)
    }
    if (newHeight < 20) {
      newHeight = 20
      newTop = y + (hasT ? h - 20 : 0)
    }

    emit('update:style', {
      ...props.defaultStyle,
      x: Math.round(newLeft),
      y: Math.round(newTop),
      w: Math.round(newWidth),
      h: Math.round(newHeight)
    })
  }

  const up = () => {
    document.removeEventListener('mousemove', move)
    document.removeEventListener('mouseup', up)
  }

  document.addEventListener('mousemove', move)
  document.addEventListener('mouseup', up)
}
</script>

<style scoped>
.shape {
  position: absolute;
  cursor: move;
  border: 1px dashed transparent;
}
.shape.active {
  border: 1px solid #1890ff;
  user-select: none;
}
.shape-point {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #fff;
  border: 1px solid #1890ff;
  border-radius: 50%;
  z-index: 1000;
}
</style>
