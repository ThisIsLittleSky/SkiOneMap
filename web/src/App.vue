<template>
  <div class="min-h-screen bg-glacier-white text-gray-800 font-sans">
    <!-- Navigation -->
    <nav class="fixed w-full z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <div class="flex-shrink-0 flex items-center gap-2">
            <Shield class="h-8 w-8 text-justice-blue" />
            <span class="font-bold text-xl text-justice-blue tracking-tight">雪境智判</span>
          </div>
          <div class="hidden md:flex space-x-8">
            <a href="#solution" class="text-gray-600 hover:text-justice-blue px-3 py-2 text-sm font-medium transition-colors">技术架构</a>
            <a href="#product" class="text-gray-600 hover:text-justice-blue px-3 py-2 text-sm font-medium transition-colors">核心产品</a>
            <a href="#services" class="text-gray-600 hover:text-justice-blue px-3 py-2 text-sm font-medium transition-colors">服务体系</a>
          </div>
          <div class="flex items-center gap-4">
             <button @click="openContactModal($event)" class="bg-justice-blue text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-800 transition-colors shadow-sm">申请B端试用</button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden bg-gradient-to-b from-blue-50 to-glacier-white">
      <div class="absolute inset-0 opacity-10 pointer-events-none">
        <!-- Placeholder for topographic/network grid background -->
        <svg class="h-full w-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1E3A8A" stroke-width="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
        <h1 class="text-[clamp(2rem,8vw,6.5rem)] font-extrabold text-gray-900 tracking-tight mb-6">
          <span class="block whitespace-nowrap">让每一片雪坡都有<span class="text-geek-green">AI的眼睛</span></span>
          <span class="block whitespace-nowrap">让每一份裁量都有<span class="text-justice-blue">有据可循</span></span>
        </h1>
        <p class="mt-4 max-w-2xl text-xl text-gray-600 mx-auto mb-10">
          从摄像头部署方案到机器视觉与RAG法律知识图谱，为滑雪场提供一站式安全预警与事故定责解决方案。
        </p>
        
        <div class="mt-10 flex justify-center gap-x-6">
          <a href="/demo.mp4" download class="rounded-md bg-justice-blue px-6 py-3 text-[clamp(0.75rem,2.2vw,1rem)] font-semibold text-white shadow-sm hover:bg-blue-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-justice-blue transition-all flex items-center gap-2">
            <PlayCircle class="w-5 h-5 shrink-0" /><span class="inline-grid"><span>观看</span><span>系统演示</span></span>
          </a>
          <a href="/雪境智判商业计划书.pdf" download class="rounded-md bg-white border border-gray-300 px-6 py-3 text-[clamp(0.75rem,2.2vw,1rem)] font-semibold text-gray-900 shadow-sm hover:bg-gray-50 transition-all flex items-center gap-2">
            <FileText class="w-5 h-5 shrink-0" /><span class="inline-grid"><span>获得</span><span>方案白皮书</span></span>
          </a>
        </div>

        <!-- Pain points stats -->
        <div class="mt-20 max-w-4xl mx-auto">
          <div class="grid grid-cols-3 gap-4 sm:gap-8">
            <div
              class="bg-white p-6 rounded-xl shadow-sm border cursor-pointer transition-all hover:shadow-md"
              :class="activePainPoint === 0 ? 'border-justice-blue shadow-md animate-pop' : 'border-gray-100'"
              @click="activePainPoint = 0"
            >
              <div class="flex flex-col items-center">
                <div class="p-3 bg-red-50 text-red-600 rounded-full mb-4">
                  <CameraOff class="w-6 h-6" />
                </div>
                <h3 class="text-lg font-semibold">举证难</h3>
              </div>
            </div>
            <div
              class="bg-white p-6 rounded-xl shadow-sm border cursor-pointer transition-all hover:shadow-md"
              :class="activePainPoint === 1 ? 'border-justice-blue shadow-md animate-pop' : 'border-gray-100'"
              @click="activePainPoint = 1"
            >
              <div class="flex flex-col items-center">
                <div class="p-3 bg-orange-50 text-orange-600 rounded-full mb-4">
                  <Scale class="w-6 h-6" />
                </div>
                <h3 class="text-lg font-semibold">定责难</h3>
              </div>
            </div>
            <div
              class="bg-white p-6 rounded-xl shadow-sm border cursor-pointer transition-all hover:shadow-md"
              :class="activePainPoint === 2 ? 'border-justice-blue shadow-md animate-pop' : 'border-gray-100'"
              @click="activePainPoint = 2"
            >
              <div class="flex flex-col items-center">
                <div class="p-3 bg-yellow-50 text-yellow-600 rounded-full mb-4">
                  <TrendingUp class="w-6 h-6" />
                </div>
                <h3 class="text-lg font-semibold">成本高</h3>
              </div>
            </div>
          </div>
          <Transition name="pain-desc" mode="out-in">
            <div :key="activePainPoint" class="mt-4 bg-white border border-gray-200 rounded-xl px-6 py-4 shadow-sm">
              <p class="text-gray-500 text-sm text-center">{{ painDescriptions[activePainPoint] }}</p>
            </div>
          </Transition>
        </div>
      </div>
    </section>

    <!-- "硬-软-法" Architecture -->
    <section id="solution" class="py-20 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-gray-900 mb-4">"硬-软-法" <span class="text-red-600">三位一体</span>架构</h2>
          <p class="text-lg text-gray-600 max-w-2xl mx-auto">解耦式设计，从物理感知到法律裁决的无缝衔接。</p>
        </div>

        <div class="grid grid-cols-3 gap-4 sm:gap-5">
          <!-- Card 1 -->
          <div
            class="group relative bg-glacier-white rounded-2xl p-5 sm:p-6 hover:shadow-lg transition-all duration-300 border overflow-hidden cursor-pointer"
            :class="activeArchLayer === 0 ? 'border-justice-blue shadow-md animate-pop' : 'border-gray-100'"
            @click="activeArchLayer = 0"
          >
             <div class="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-blue-100 rounded-full opacity-50 group-hover:scale-150 transition-transform duration-500"></div>
             <div class="relative z-10 flex flex-col items-center text-center">
              <div class="w-12 h-12 bg-white rounded-lg shadow-sm flex items-center justify-center mb-6 text-justice-blue">
                <Radar class="w-6 h-6" />
              </div>
              <h3 class="text-xl font-bold text-gray-900 leading-tight">感知层<br/>运筹学点位</h3>
            </div>
          </div>

          <!-- Card 2 -->
          <div
            class="group relative bg-glacier-white rounded-2xl p-5 sm:p-6 hover:shadow-lg transition-all duration-300 border overflow-hidden cursor-pointer"
            :class="activeArchLayer === 1 ? 'border-justice-blue shadow-md animate-pop' : 'border-gray-100'"
            @click="activeArchLayer = 1"
          >
             <div class="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-green-100 rounded-full opacity-50 group-hover:scale-150 transition-transform duration-500"></div>
             <div class="relative z-10 flex flex-col items-center text-center">
              <div class="w-12 h-12 bg-white rounded-lg shadow-sm flex items-center justify-center mb-6 text-geek-green">
                <Cpu class="w-6 h-6" />
              </div>
              <h3 class="text-xl font-bold text-gray-900 leading-tight">计算层<br/>视觉引擎</h3>
            </div>
          </div>

          <!-- Card 3 -->
          <div
            class="group relative bg-glacier-white rounded-2xl p-5 sm:p-6 hover:shadow-lg transition-all duration-300 border overflow-hidden cursor-pointer"
            :class="activeArchLayer === 2 ? 'border-justice-blue shadow-md animate-pop' : 'border-gray-100'"
            @click="activeArchLayer = 2"
          >
             <div class="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-indigo-100 rounded-full opacity-50 group-hover:scale-150 transition-transform duration-500"></div>
             <div class="relative z-10 flex flex-col items-center text-center">
              <div class="w-12 h-12 bg-white rounded-lg shadow-sm flex items-center justify-center mb-6 text-indigo-600">
                <BookOpen class="w-6 h-6" />
              </div>
              <h3 class="text-xl font-bold text-gray-900 leading-tight">决策层<br/>法律大脑</h3>
            </div>
          </div>
        </div>
        <Transition name="pain-desc" mode="out-in">
          <div :key="activeArchLayer" class="mt-4 bg-white border border-gray-200 rounded-xl px-6 py-4 shadow-sm">
            <p class="text-gray-600 text-sm leading-relaxed mb-3 text-center">{{ archDetails[activeArchLayer].desc }}</p>
            <ul class="flex justify-center gap-6 text-sm text-gray-500">
              <li v-for="item in archDetails[activeArchLayer].items" :key="item" class="flex items-center gap-2"><CheckCircle2 class="w-4 h-4 text-geek-green" /> {{ item }}</li>
            </ul>
          </div>
        </Transition>
      </div>
    </section>

    <!-- AI Models Ecosystem -->
    <section class="py-20 bg-white overflow-hidden">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-8 sm:mb-16">
          <h2 class="text-3xl font-bold text-gray-900 mb-4"><span class="block text-red-600">一个入口，</span><span class="block">兼容所有<span class="text-geek-green">AI</span>与<span class="text-justice-blue">摄像头品牌</span></span></h2>
          <p class="text-lg text-gray-600 max-w-2xl mx-auto">无缝兼容300+主流大语言模型、多模态模型、大视觉模型、摄像头视频流接口</p>
        </div>
        <div class="relative mx-auto h-[320px] w-[320px] sm:h-[500px] sm:w-[500px] lg:h-[600px] lg:w-[600px]">
          <!-- Concentric circles (static) -->
          <div class="absolute inset-0 rounded-full border border-gray-200"></div>
          <div class="absolute inset-[25%] rounded-full border border-gray-200"></div>
          <!-- Rotating icons layer -->
          <div class="absolute inset-0" style="animation: spin-slow 30s linear infinite;">
            <div
              v-for="icon in outerIcons"
              :key="icon.name"
              class="absolute -translate-x-1/2 -translate-y-1/2"
              :style="{ left: icon.left, top: icon.top }"
            >
              <div
                class="flex h-14 w-14 items-center justify-center rounded-full border border-gray-200 bg-white shadow-sm sm:h-16 sm:w-16 lg:h-[4.5rem] lg:w-[4.5rem]"
                style="animation: spin-slow 30s linear infinite reverse;"
              >
                <img :src="icon.src" :alt="icon.name" :title="icon.name" class="h-7 w-7 object-contain sm:h-8 sm:w-8 lg:h-9 lg:w-9" />
              </div>
            </div>
            <div
              v-for="icon in innerIcons"
              :key="icon.name"
              class="absolute -translate-x-1/2 -translate-y-1/2"
              :style="{ left: icon.left, top: icon.top }"
            >
              <div
                class="flex h-11 w-11 items-center justify-center rounded-full border border-gray-200 bg-white shadow-sm sm:h-[3.25rem] sm:w-[3.25rem] lg:h-14 lg:w-14"
                style="animation: spin-slow 30s linear infinite reverse;"
              >
                <img :src="icon.src" :alt="icon.name" :title="icon.name" class="h-5 w-5 object-contain sm:h-6 sm:w-6 lg:h-7 lg:w-7" />
              </div>
            </div>
          </div>
          <!-- Center text (static) -->
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="text-center">
              <div class="text-4xl font-bold text-red-500 sm:text-5xl lg:text-6xl">300+</div>
              <div class="text-gray-500 mt-1 text-sm sm:text-base">Models</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Product Flow -->
    <section id="product" class="py-20 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-gray-900 mb-4">一张图，掌握全局态势</h2>
          <p class="text-lg text-gray-600 max-w-2xl mx-auto">全链路闭环流程，从报警到存证一气呵成。</p>
        </div>

        <!-- Flowchart UI -->
        <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-4 sm:p-6 md:p-8 lg:p-12">
          <div class="flex flex-row items-center justify-between gap-1 sm:gap-2 md:gap-4 relative">

            <!-- Connection Line -->
            <div class="absolute top-1/2 left-0 w-full h-0.5 sm:h-1 bg-gray-100 -translate-y-1/2 z-0"></div>

            <div class="relative z-10 flex flex-col items-center bg-white px-0.5 sm:px-2">
              <div class="w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 rounded-full bg-red-100 text-red-600 flex items-center justify-center mb-1 sm:mb-2 lg:mb-3 shadow-sm border-2 sm:border-4 border-white animate-wave" style="animation-delay: 0s;">
                <AlertTriangle class="w-6 h-6 sm:w-7 sm:h-7 lg:w-8 lg:h-8" />
              </div>
              <span class="text-xs sm:text-sm lg:text-base font-medium text-gray-900">事故报警</span>
            </div>

            <div class="relative z-10 flex flex-col items-center bg-white px-0.5 sm:px-2">
              <div class="w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mb-1 sm:mb-2 lg:mb-3 shadow-sm border-2 sm:border-4 border-white animate-wave" style="animation-delay: 0.6s;">
                <Video class="w-6 h-6 sm:w-7 sm:h-7 lg:w-8 lg:h-8" />
              </div>
              <span class="text-xs sm:text-sm lg:text-base font-medium text-gray-900">轨迹提取</span>
            </div>

            <div class="relative z-10 flex flex-col items-center bg-white px-0.5 sm:px-2">
              <div class="w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-1 sm:mb-2 lg:mb-3 shadow-sm border-2 sm:border-4 border-white animate-wave" style="animation-delay: 1.2s;">
                <Gavel class="w-6 h-6 sm:w-7 sm:h-7 lg:w-8 lg:h-8" />
              </div>
              <span class="text-xs sm:text-sm lg:text-base font-medium text-gray-900">规则匹配</span>
            </div>

            <div class="relative z-10 flex flex-col items-center bg-white px-0.5 sm:px-2">
              <div class="w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 rounded-full bg-green-100 text-geek-green flex items-center justify-center mb-1 sm:mb-2 lg:mb-3 shadow-sm border-2 sm:border-4 border-white animate-wave" style="animation-delay: 1.8s;">
                <PieChart class="w-6 h-6 sm:w-7 sm:h-7 lg:w-8 lg:h-8" />
              </div>
              <span class="text-xs sm:text-sm lg:text-base font-medium text-gray-900">责任量化</span>
            </div>

            <div class="relative z-10 flex flex-col items-center bg-white px-0.5 sm:px-2">
              <div class="w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center mb-1 sm:mb-2 lg:mb-3 shadow-sm border-2 sm:border-4 border-white animate-wave" style="animation-delay: 2.4s;">
                <LinkIcon class="w-6 h-6 sm:w-7 sm:h-7 lg:w-8 lg:h-8" />
              </div>
              <span class="text-xs sm:text-sm lg:text-base font-medium text-gray-900">司法存证</span>
            </div>

          </div>

          <div class="mt-16 bg-gray-900 rounded-xl p-4 overflow-hidden shadow-2xl border border-gray-800 relative">
            <div class="flex items-center gap-2 mb-4 px-2">
              <div class="w-3 h-3 rounded-full bg-red-500"></div>
              <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
              <div class="w-3 h-3 rounded-full bg-green-500"></div>
              <span class="text-gray-400 text-xs ml-2 font-mono">dashboard.ai-ski.system</span>
            </div>
            <div ref="containerRef" class="aspect-video bg-gray-800 rounded-lg flex items-center justify-center border border-gray-700 relative overflow-hidden">
               <!-- State: Idle -->
               <template v-if="viewerState === 'idle'">
                 <div class="absolute inset-0 opacity-20 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4IiBoZWlnaHQ9IjgiPgo8cmVjdCB3aWR0aD0iOCIgaGVpZ2h0PSI4IiBmaWxsPSIjZmZmIiBmaWxsLW9wYWNpdHk9IjAuMCIvPgo8cGF0aCBkPSJNMCAwbDhfOHptOCAwTDBfOHoiIHN0cm9rZT0iIzAwMCIgc3Ryb2tlLW9wYWNpdHk9IjAuMSIvPgo8L3N2Zz4=')]"></div>
                 <div class="text-center z-10">
                    <Monitor class="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <p class="text-gray-400 font-medium">雪境智判 3D 实时态势感知孪生建模演示（仅演示非正式产品）</p>
                    <button @click="startViewer" class="mt-4 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded text-sm transition border border-white/20 backdrop-blur-sm">点击互动</button>
                 </div>
               </template>

               <!-- State: Loading -->
               <template v-else-if="viewerState === 'loading'">
                 <div class="text-center z-10 px-8 w-full max-w-sm">
                    <p class="text-white font-medium mb-4">正在加载 3D 模型...</p>
                    <template v-if="loadProgress >= 0">
                      <div class="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                        <div class="bg-justice-blue h-full rounded-full transition-all duration-300" :style="{ width: loadProgress + '%' }"></div>
                      </div>
                      <p class="text-gray-400 text-xs mt-2">{{ loadProgress }}%</p>
                    </template>
                    <template v-else>
                      <div class="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                        <div class="bg-justice-blue h-full rounded-full animate-pulse" style="width: 60%"></div>
                      </div>
                      <p class="text-gray-400 text-xs mt-2">正在解析模型文件...</p>
                    </template>
                    <p class="text-gray-500 text-xs mt-4">模型文件较大（约28MB），请耐心等待</p>
                 </div>
               </template>

               <!-- State: Error -->
               <template v-else-if="viewerState === 'error'">
                 <div class="text-center z-10 px-8">
                    <p class="text-red-400 font-medium mb-2">模型加载失败</p>
                    <p class="text-gray-400 text-sm mb-4">{{ errorMessage }}</p>
                    <button @click="startViewer" class="mt-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded text-sm transition border border-white/20 backdrop-blur-sm">重试</button>
                 </div>
               </template>

               <!-- State: Loaded -->
               <template v-else>
                 <div class="absolute right-3 top-1/2 -translate-y-1/2 z-20 flex flex-col items-center gap-1">
                    <span class="text-gray-300 text-xs leading-none select-none">+</span>
                    <input
                      type="range"
                      :value="zoomLevel"
                      @input="onZoomChange"
                      class="zoom-slider"
                      min="0"
                      max="100"
                    />
                    <span class="text-gray-300 text-xs leading-none select-none">-</span>
                 </div>
               </template>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- B2B Services -->
    <section id="services" class="py-20 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-gray-900 mb-4">赋能行业，降本增效</h2>
          <p class="text-lg text-gray-600 max-w-2xl mx-auto">为雪场提供一站式智能化升级与合规托管服务。</p>
        </div>

        <div class="max-w-2xl mx-auto">
          <!-- B2B -->
          <div class="border border-gray-200 rounded-2xl p-8 lg:p-10 bg-gradient-to-br from-white to-blue-50 shadow-sm">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 text-justice-blue text-sm font-bold mb-6">
              <Building2 class="w-4 h-4" /> B2B 企业端
            </div>
            <h3 class="text-2xl font-bold text-gray-900 mb-4">数字模型赋能与合规托管</h3>
            <p class="text-gray-600 mb-8">助力滑雪场实现监控智能化升级，降低安全巡检人力与法务成本。</p>

            <ul class="space-y-4 mb-8">
              <li class="flex items-start gap-3">
                <CheckCircle2 class="w-5 h-5 text-justice-blue shrink-0 mt-0.5" />
                <span class="text-gray-700"><strong class="font-semibold">基础版：</strong>核心区域监控、基础碰撞预警</span>
              </li>
              <li class="flex items-start gap-3">
                <CheckCircle2 class="w-5 h-5 text-justice-blue shrink-0 mt-0.5" />
                <span class="text-gray-700"><strong class="font-semibold">专业版：</strong>全域轨迹追踪、多维数据分析报表</span>
              </li>
              <li class="flex items-start gap-3">
                <CheckCircle2 class="w-5 h-5 text-justice-blue shrink-0 mt-0.5" />
                <span class="text-gray-700"><strong class="font-semibold">旗舰版：</strong>API深度集成、驻场法务顾问辅助</span>
              </li>
            </ul>
            <button @click="openContactModal($event)" class="w-full bg-justice-blue text-white rounded-lg py-3 font-medium hover:bg-blue-800 transition shadow-sm">申请盲区摸排方案</button>
          </div>
        </div>
      </div>
    </section>

    <!-- Team Members -->
    <section class="py-20 bg-gray-50 border-t border-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="mx-auto mb-12 max-w-3xl text-center">
          <h2 class="text-3xl font-bold text-gray-900 mb-3">与<span class="text-red-600">优秀</span>的人同行</h2>
          <p class="text-gray-500 text-base">感谢每一位团队成员的热情与付出</p>
        </div>
        <div class="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-8 lg:grid-cols-10 gap-2 sm:gap-3">
          <div v-for="member in teamMembers" :key="member.name" :title="`${member.name}: ${member.role}`" class="border border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/30 group flex flex-col items-center gap-1.5 rounded-lg p-2 transition-all duration-300 sm:p-3">
            <img v-if="member.avatar" :src="member.avatar" :alt="member.name" class="h-10 w-10 sm:h-12 sm:w-12 rounded-full ring-2 ring-gray-200 group-hover:ring-blue-400 transition-all duration-300 object-cover">
            <div v-else class="h-10 w-10 sm:h-12 sm:w-12 rounded-full ring-2 ring-gray-200 group-hover:ring-blue-400 transition-all duration-300 flex items-center justify-center bg-gradient-to-br from-blue-100 to-blue-200">
              <span class="text-blue-600 font-bold text-xs sm:text-sm">{{ member.name.charAt(0) }}</span>
            </div>
            <span class="text-gray-500 group-hover:text-gray-900 max-w-full truncate text-xs transition-colors sm:text-sm" style="font-family: 'SimHei', '黑体', 'Microsoft YaHei', sans-serif; font-weight: bold;">{{ member.name }}</span>
            <span class="text-black text-[10px] sm:text-xs">{{ member.role }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Open Source / Join Us -->
    <section class="py-16 bg-white border-t border-gray-100">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-10">
          <h2 class="text-3xl font-bold text-gray-900 mb-2"><span class="text-red-600">代码开源</span>，我们要超越自己</h2>
          <h2 class="text-3xl font-bold text-gray-900 mb-2">成为<span class="text-justice-blue"> 雪境智判 </span>的一员</h2>
          <p class="text-gray-500">为雪道安全监测与辅助划责贡献自己的一份力</p>
        </div>

        <a
          href="https://github.com/ThisIsLittleSky/SkiOneMap"
          target="_blank"
          rel="noopener noreferrer"
          class="group block rounded-xl border border-gray-200 bg-[#0d1117] hover:border-gray-400 hover:shadow-lg transition-all duration-300 overflow-hidden"
        >
          <!-- Card header bar -->
          <div class="flex items-center gap-2 px-5 py-3 bg-[#161b22] border-b border-gray-700/60">
            <Github class="w-5 h-5 text-gray-400" />
            <span class="text-sm text-gray-400 font-mono">ThisIsLittleSky / <span class="text-white font-semibold">SkiOneMap</span></span>
            <span class="ml-auto px-2 py-0.5 text-[11px] rounded-full border border-gray-600 text-gray-400 font-mono">Public</span>
          </div>

          <!-- Card body -->
          <div class="px-5 py-5">
            <div class="flex items-start gap-4">
              <div class="shrink-0 mt-1">
                <div class="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-xl">
                  ❄️
                </div>
              </div>
              <div class="min-w-0">
                <h3 class="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors inline-flex items-center gap-2">
                  SkiOneMap
                  <ExternalLink class="w-4 h-4 opacity-0 -translate-y-1 translate-x-1 group-hover:opacity-100 group-hover:translate-y-0 group-hover:translate-x-0 transition-all duration-200" />
                </h3>
                <p class="text-gray-400 text-sm mt-1 leading-relaxed">
                  雪境智判 —— 基于 YOLO11 视觉引擎与 RAG 法律知识图谱的雪道安全监测与事故定责辅助系统。
                </p>
                <div class="flex flex-wrap items-center gap-5 mt-4 text-[13px] text-gray-500">
                  <span class="flex items-center gap-1.5">
                    <span class="w-3 h-3 rounded-full bg-green-500"></span>
                    Vue
                  </span>
                  <span class="flex items-center gap-1.5">
                    <Star class="w-4 h-4" />
                    3
                  </span>
                  <span class="flex items-center gap-1.5">
                    <GitFork class="w-4 h-4" />
                    0
                  </span>
                  <span class="flex items-center gap-1.5 text-blue-400 group-hover:text-blue-300 transition-colors font-medium">
                    <ExternalLink class="w-3.5 h-3.5" />
                    查看仓库
                  </span>
                </div>
              </div>
            </div>
          </div>
        </a>
      </div>
    </section>

    <!-- Trust & Security -->
    <section class="py-16 bg-white border-t border-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-center text-xl font-semibold text-gray-500 mb-10 tracking-wider">权威背书 与 隐私保障</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div class="flex flex-col items-center text-center">
            <ShieldCheck class="w-10 h-10 text-gray-400 mb-3" />
            <h4 class="font-medium text-gray-900">边缘脱敏技术</h4>
            <p class="text-xs text-gray-500 mt-1">原始视频不上云，仅提取骨骼行为特征，保障用户隐私。</p>
          </div>
          <div class="flex flex-col items-center text-center">
            <Scale class="w-10 h-10 text-gray-400 mb-3" />
            <h4 class="font-medium text-gray-900">合规辅具定位</h4>
            <p class="text-xs text-gray-500 mt-1">报告作为"专家辅助人意见"参考，严格遵守法律规范。</p>
          </div>
          <div class="flex flex-col items-center text-center">
            <Award class="w-10 h-10 text-gray-400 mb-3" />
            <h4 class="font-medium text-gray-900">知识产权背书</h4>
            <p class="text-xs text-gray-500 mt-1">多项国家发明专利与软著保护，核心技术自主可控。</p>
          </div>
          <div class="flex flex-col items-center text-center">
            <Trophy class="w-10 h-10 text-gray-400 mb-3" />
            <h4 class="font-medium text-gray-900">行业认可</h4>
            <p class="text-xs text-gray-500 mt-1">"挑战杯"等顶级竞赛荣誉，产学研深度融合成果。</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-50 border-t border-gray-200 pt-16 pb-8">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          <div>
            <p class="text-gray-700 max-w-sm tracking-wide" style="font-family: 'Ma Shan Zheng', KaiTi, STKaiti, cursive; font-size: 1.5rem; font-weight: 700;">
              雪境智判的理念：<br>致力于用人工智能与法律科技，为冰雪运动提供坚实的安全与维权后盾。
            </p>
          </div>
          <div class="flex flex-row gap-6 sm:gap-8">
            <div class="flex-1">
              <h4 class="font-semibold text-gray-900 mb-4">产品服务</h4>
              <ul class="space-y-2 text-sm text-gray-500">
                <li><a href="#" class="hover:text-justice-blue">虚拟仿真雪场数字化方案</a></li>
                <li><a href="#" class="hover:text-justice-blue">RAG法律咨询agent</a></li>
              </ul>
            </div>
            <div class="flex-1">
              <h4 class="font-semibold text-gray-900 mb-4">合作伙伴</h4>
              <ul class="space-y-2 text-sm text-gray-500">
                <li>海康威视 (硬件支持)</li>
                <li>中国裁判文书网 (数据合作)</li>
                <li>地方滑雪协会</li>
              </ul>
            </div>
          </div>
        </div>
        <div class="border-t border-gray-200 pt-8 space-y-4">
          <div class="flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-gray-400">
            <p>© 2026 雪境智判团队. 保留所有权利。</p>
            <div class="flex gap-4">
              <a href="#" class="hover:text-gray-600">隐私政策</a>
              <a href="#" class="hover:text-gray-600">服务条款</a>
            </div>
          </div>
          <div class="flex flex-wrap justify-center items-center gap-x-6 gap-y-2 text-xs text-gray-400">
            <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer" class="hover:text-gray-600">冀ICP备2024079391号</a>
            <a href="http://www.beian.gov.cn/portal/registerSystemInfo?recordcode=13062302000122" target="_blank" rel="noopener noreferrer" class="hover:text-gray-600 inline-flex items-center gap-1">
              <img src="https://beian.mps.gov.cn/web/assets/logo01.6189a29f.png" alt="备案图标" class="h-4 w-4" />
              冀公网安备13062302000122号
            </a>
          </div>
        </div>
      </div>
    </footer>

    <!-- Contact Modal -->
    <Teleport to="body">
      <Transition
        @before-enter="onModalBeforeEnter"
        @enter="onModalEnter"
        @after-enter="onModalAfterEnter"
        @before-leave="onModalBeforeLeave"
        @leave="onModalLeave"
        @after-leave="onModalAfterLeave"
      >
        <div
          v-if="showContactModal"
          class="fixed inset-0 z-[100] flex items-center justify-center"
          @click.self="closeContactModal"
        >
          <!-- backdrop -->
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" />
          <!-- card -->
          <div
            ref="modalCardRef"
            class="relative bg-white rounded-2xl shadow-2xl max-w-sm w-full mx-4 overflow-hidden"
          >
            <button
              @click="closeContactModal"
              class="absolute top-3 right-3 z-10 w-8 h-8 flex items-center justify-center rounded-full bg-black/10 hover:bg-black/20 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <X class="w-5 h-5" />
            </button>
            <div class="p-6">
              <h3 class="text-lg font-bold text-gray-900 mb-4 text-center">申请B端使用</h3>
              <img
                src="/联系方式.jpg"
                alt="联系方式"
                class="w-full rounded-lg"
              />
              <p class="text-gray-500 text-sm text-center mt-4">请扫码或保存图片联系工作人员</p>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import {
  Shield, 
  PlayCircle, 
  FileText, 
  CameraOff, 
  Scale, 
  TrendingUp, 
  Radar, 
  Cpu, 
  BookOpen, 
  CheckCircle2,
  AlertTriangle,
  Video,
  Gavel,
  PieChart,
  LinkIcon,
  Monitor,
  Building2,
  ShieldCheck,
  Award,
  Trophy,
  Github,
  Star,
  GitFork,
  ExternalLink,
  X
} from 'lucide-vue-next'
import { outerIcons, innerIcons } from './data/aiIcons.js'

// --- Team Members Data ---
const teamMembers = ref([
  { name: '耿喆', role: '项目负责人', avatar: '/耿喆-项目负责人.jpg' },
  { name: '李格含', role: '商业模式战略分析', avatar: '/李格含-商业模式战略分析.jpg' },
  { name: '李子卓', role: '法律知识研究与司法解释建议', avatar: '/李子卓-法律知识研究与司法解释建议.jpg' },
  { name: '李婧妍', role: '项目市场运营与材料审计', avatar: '/李婧妍-项目市场运营与材料审计.jpg' },
  { name: '刘娜', role: '摄像头调度数学建模', avatar: '/刘娜-摄像头调度数学建模.jpg' },
  { name: '杜雨彤', role: '财务', avatar: '/杜雨彤-财务.jpg' },
  { name: '周子天', role: '系统架构与算法', avatar: '/周子天-系统架构与算法.jpg' },
])

// --- Contact Modal ---
const activePainPoint = ref<number>(0)
let painTimer: ReturnType<typeof setInterval> | null = null
const painDescriptions = [
  '传统监控盲区大，事故瞬间难捕捉，缺乏客观视觉证据。',
  '滑雪规则专业性强，碰撞瞬间速度/角度难以肉眼量化，权责不清。',
  '全覆盖改造硬件成本极高，后期纠纷处理耗费大量人力法务资源。',
]

const activeArchLayer = ref<number>(0)
let archTimer: ReturnType<typeof setInterval> | null = null
const archDetails = [
  {
    desc: '基于运筹学模型实现摄像头无盲区部署最优解。支持利旧改造，兼容现有监控网络。',
    items: ['消除99%盲区', '削减80%硬件成本'],
  },
  {
    desc: '自研优化 YOLO11 算法，无惧风雪与强光。精准识别滑雪者行为、计算瞬时速度与横切角度。',
    items: ['毫秒级行为分析', '复杂天气高鲁棒性'],
  },
  {
    desc: '基于3000+真实判例构建法律知识图谱。自动匹配国际雪联规则与国内法规，量化责任比例。',
    items: ['自动生成分析意见书', '辅助司法调解参考'],
  },
]

const showContactModal = ref(false)
const modalCardRef = ref<HTMLDivElement | null>(null)
const triggerRect = ref<DOMRect | null>(null)

function openContactModal(e: MouseEvent) {
  const el = e.currentTarget as HTMLElement
  triggerRect.value = el.getBoundingClientRect()
  showContactModal.value = true
}

function closeContactModal() {
  showContactModal.value = false
}

function snapCardToRect(card: HTMLElement, r: DOMRect) {
  card.style.position = 'fixed'
  card.style.left = r.left + 'px'
  card.style.top = r.top + 'px'
  card.style.width = r.width + 'px'
  card.style.height = r.height + 'px'
  card.style.margin = '0'
  card.style.maxWidth = 'none'
  card.style.borderRadius = '8px'
  card.style.transform = 'scale(1) rotateY(0deg)'
  card.style.transition = 'none'
}

function measureNaturalCard(card: HTMLElement): DOMRect {
  const prev = {
    width: card.style.width,
    height: card.style.height,
    maxWidth: card.style.maxWidth,
    margin: card.style.margin,
    position: card.style.position,
    left: card.style.left,
    top: card.style.top,
    borderRadius: card.style.borderRadius,
    transform: card.style.transform,
  }
  // let the card assume its natural CSS layout size
  card.style.width = ''
  card.style.height = ''
  card.style.maxWidth = ''
  card.style.margin = ''
  card.style.position = ''
  card.style.left = ''
  card.style.top = ''
  card.style.borderRadius = ''
  card.style.transform = ''
  const natural = card.getBoundingClientRect()
  // restore previous inline styles
  Object.assign(card.style, prev)
  return natural
}

function onModalBeforeEnter(el: Element) {
  const card = (el as HTMLElement).querySelector('.relative') as HTMLElement
  if (!card || !triggerRect.value) return
  snapCardToRect(card, triggerRect.value)
  const content = card.querySelector('.p-6') as HTMLElement
  if (content) content.style.opacity = '0'
  const backdrop = (el as HTMLElement).querySelector('.absolute') as HTMLElement
  if (backdrop) backdrop.style.opacity = '0'
}

function onModalEnter(el: Element, done: () => void) {
  const card = (el as HTMLElement).querySelector('.relative') as HTMLElement
  if (!card) { done(); return }

  // measure natural size at center, then reset to button position
  const natural = measureNaturalCard(card)
  const targetLeft = (window.innerWidth - natural.width) / 2
  const targetTop = (window.innerHeight - natural.height) / 2

  // reflow so the starting (button-sized) state paints before we animate
  card.offsetHeight

  card.style.transition = 'all 0.5s cubic-bezier(0.22, 0.61, 0.36, 1)'
  card.style.left = targetLeft + 'px'
  card.style.top = targetTop + 'px'
  card.style.width = natural.width + 'px'
  card.style.height = natural.height + 'px'
  card.style.maxWidth = ''
  card.style.borderRadius = ''
  card.style.transform = ''
  card.style.margin = ''

  const backdrop = (el as HTMLElement).querySelector('.absolute') as HTMLElement
  if (backdrop) {
    backdrop.style.transition = 'opacity 0.5s ease'
    backdrop.style.opacity = ''
  }
  const content = card.querySelector('.p-6') as HTMLElement
  if (content) {
    content.style.transition = 'opacity 0.25s ease 0.25s'
    content.style.opacity = ''
  }

  const handleDone = () => {
    card.removeEventListener('transitionend', handleDone)
    done()
  }
  card.addEventListener('transitionend', handleDone)
}

function onModalAfterEnter(_el: Element) {
  const card = modalCardRef.value
  if (!card) return
  card.style.transition = ''
  card.style.left = ''
  card.style.top = ''
  card.style.position = ''
  card.style.width = ''
  card.style.height = ''
  card.style.maxWidth = ''
  card.style.borderRadius = ''
  card.style.margin = ''
  card.style.transform = ''
}

function onModalBeforeLeave(el: Element) {
  const card = (el as HTMLElement).querySelector('.relative') as HTMLElement
  if (!card || !triggerRect.value) return
  const cardRect = card.getBoundingClientRect()
  // pin current position so we can animate away from it
  card.style.position = 'fixed'
  card.style.left = cardRect.left + 'px'
  card.style.top = cardRect.top + 'px'
  card.style.width = cardRect.width + 'px'
  card.style.height = cardRect.height + 'px'
  card.style.margin = '0'
  card.style.maxWidth = 'none'
  card.style.transition = 'none'
  card.offsetHeight

  const r = triggerRect.value
  card.style.transition = 'all 0.35s cubic-bezier(0.55, 0.06, 0.68, 0.19)'
  card.style.left = r.left + 'px'
  card.style.top = r.top + 'px'
  card.style.width = r.width + 'px'
  card.style.height = r.height + 'px'
  card.style.borderRadius = '8px'
  card.style.transform = 'scale(0.95)'

  const backdrop = (el as HTMLElement).querySelector('.absolute') as HTMLElement
  if (backdrop) {
    backdrop.style.transition = 'opacity 0.3s ease'
    backdrop.style.opacity = '0'
  }
  const content = card.querySelector('.p-6') as HTMLElement
  if (content) {
    content.style.transition = 'opacity 0.12s ease'
    content.style.opacity = '0'
  }
}

function onModalLeave(el: Element, done: () => void) {
  const card = (el as HTMLElement).querySelector('.relative') as HTMLElement
  if (!card) { done(); return }
  const handleDone = () => {
    card.removeEventListener('transitionend', handleDone)
    done()
  }
  card.addEventListener('transitionend', handleDone)
}

function onModalAfterLeave(_el: Element) {
  triggerRect.value = null
}

// --- 3D Viewer State ---
const containerRef = ref<HTMLDivElement | null>(null)
const viewerState = ref<'idle' | 'loading' | 'loaded' | 'error'>('idle')
const loadProgress = ref(-1)
const errorMessage = ref('')
const zoomLevel = ref(50)

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: OrbitControls | null = null
let resizeObserver: ResizeObserver | null = null
let baseDistance = 5
let minZoomDist = 1
let maxZoomDist = 15

function onResize() {
  if (!containerRef.value || !renderer || !camera) return
  const w = containerRef.value.clientWidth
  const h = containerRef.value.clientHeight
  if (w === 0 || h === 0) return
  renderer.setSize(w, h, false)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

function onZoomChange(e: Event) {
  const target = e.target as HTMLInputElement
  const value = parseInt(target.value)
  zoomLevel.value = value
  const t = value / 100
  const newDist = minZoomDist + t * (maxZoomDist - minZoomDist)
  const dir = camera!.position.clone().sub(controls!.target).normalize()
  camera!.position.copy(controls!.target).addScaledVector(dir, newDist)
  controls!.update()
}

function disposeMaterial(material: THREE.Material) {
  for (const key of Object.keys(material)) {
    const value = (material as Record<string, unknown>)[key]
    if (value instanceof THREE.Texture) {
      value.dispose()
    }
  }
  material.dispose()
}

function cleanupThree() {
  if (renderer) {
    renderer.setAnimationLoop(null)
  }
  if (controls) {
    controls.dispose()
    controls = null
  }
  if (scene) {
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        object.geometry?.dispose()
        if (Array.isArray(object.material)) {
          object.material.forEach(m => disposeMaterial(m))
        } else {
          disposeMaterial(object.material as THREE.Material)
        }
      }
    })
    scene.clear()
    scene = null
  }
  if (renderer) {
    renderer.domElement.remove()
    renderer.dispose()
    renderer = null
  }
  camera = null
}

function initThreeRenderer() {
  const container = containerRef.value!
  const width = container.clientWidth
  const height = container.clientHeight

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(width, height, false)
  renderer.setClearColor(new THREE.Color(0x1f2937))

  renderer.domElement.style.position = 'absolute'
  renderer.domElement.style.inset = '0'
  renderer.domElement.style.width = '100%'
  renderer.domElement.style.height = '100%'
  container.appendChild(renderer.domElement)
}

function initScene() {
  const container = containerRef.value!
  scene = new THREE.Scene()

  camera = new THREE.PerspectiveCamera(
    45,
    container.clientWidth / container.clientHeight,
    0.1,
    1000
  )
  camera.position.set(5, 3, 8)

  const ambient = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambient)

  const directional = new THREE.DirectionalLight(0xffffff, 1.2)
  directional.position.set(5, 10, 7)
  scene.add(directional)

  const fill = new THREE.DirectionalLight(0xffffff, 0.3)
  fill.position.set(-3, -1, -5)
  scene.add(fill)

  controls = new OrbitControls(camera, renderer!.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.minDistance = 0.5
  controls.maxDistance = 50
  controls.target.set(0, 0, 0)
  controls.update()
}

function loadModel(): Promise<void> {
  return new Promise((resolve, reject) => {
    const loader = new GLTFLoader()
    loader.load(
      '/7秒换视角.glb',
      (gltf) => {
        const model = gltf.scene
        const box = new THREE.Box3().setFromObject(model)
        const center = new THREE.Vector3()
        box.getCenter(center)
        const size = new THREE.Vector3()
        box.getSize(size)

        model.position.sub(center)

        const maxDim = Math.max(size.x, size.y, size.z)
        const fov = camera!.fov * (Math.PI / 180)
        const distance = maxDim / (2 * Math.tan(fov / 2)) * 1.5
        camera!.position.set(distance * 0.8, distance * 0.4, distance)
        camera!.lookAt(0, 0, 0)
        controls!.target.set(0, 0, 0)
        controls!.update()

        baseDistance = distance
        minZoomDist = distance * 0.1
        maxZoomDist = distance * 3
        zoomLevel.value = 50

        scene!.add(model)
        resolve()
      },
      (progressEvent) => {
        if (progressEvent.total > 0) {
          loadProgress.value = Math.round((progressEvent.loaded / progressEvent.total) * 100)
        }
      },
      (errorEvent) => {
        reject(new Error(errorEvent instanceof ErrorEvent
          ? errorEvent.message
          : 'GLB 文件加载失败，请检查网络或文件完整性'))
      }
    )
  })
}

function startRenderLoop() {
  renderer!.setAnimationLoop(() => {
    controls!.update()
    renderer!.render(scene!, camera!)
  })
}

async function startViewer() {
  if (viewerState.value === 'loading') return
  viewerState.value = 'loading'
  loadProgress.value = -1

  await nextTick()

  try {
    initThreeRenderer()
    initScene()
    await loadModel()
    startRenderLoop()
    viewerState.value = 'loaded'
  } catch (err: unknown) {
    console.error('3D viewer error:', err)
    errorMessage.value = err instanceof Error ? err.message : '未知错误，请检查控制台'
    viewerState.value = 'error'
    cleanupThree()
  }
}

onMounted(() => {
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => onResize())
    resizeObserver.observe(containerRef.value)
  }
  painTimer = setInterval(() => {
    activePainPoint.value = (activePainPoint.value + 1) % 3
  }, 3000)
  archTimer = setInterval(() => {
    activeArchLayer.value = (activeArchLayer.value + 1) % 3
  }, 4000)
})

onBeforeUnmount(() => {
  cleanupThree()
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (painTimer) {
    clearInterval(painTimer)
    painTimer = null
  }
  if (archTimer) {
    clearInterval(archTimer)
    archTimer = null
  }
})
</script>

<style scoped>
.zoom-slider {
  writing-mode: vertical-lr;
  direction: rtl;
  height: 180px;
  width: 4px;
  cursor: pointer;
  accent-color: #1E3A8A;
  appearance: slider-vertical;
}

.pain-desc-enter-active {
  transition: all 0.3s ease-out;
}
.pain-desc-leave-active {
  transition: all 0.2s ease-in;
}
.pain-desc-enter-from {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}
@keyframes pop {
  0%   { transform: scale(1); }
  40%  { transform: scale(1.06); }
  100% { transform: scale(1); }
}
.animate-pop {
  animation: pop 0.35s ease-out;
}

.pain-desc-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}
</style>
