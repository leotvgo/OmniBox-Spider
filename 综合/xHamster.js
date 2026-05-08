
/**
 * xHamster 中文站 OmniBox Spider
 * 站点：https://zh.xhamster.com
 * 
 * 特性：
 * - 首页推荐
 * - 分类浏览 (支持按字母、国家、标签)
 * - 视频搜索
 * - 播放地址提取 (支持 m3u8/mp4 多清晰度)
 * 
 * 使用说明：
 * 1. 将此文件放入 OmniBox 的 spiders 目录
 * 2. 在 OmniBox 中添加此源
 * 3. 支持搜索、分类、播放等功能
 */

const { Spider, request, cheerio } = require('sdk');

class XHamsterSpider extends Spider {
  constructor() {
    super();
    this.site = 'https://zh.xhamster.com';
    this.headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Referer': 'https://zh.xhamster.com/',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
      'Connection': 'keep-alive',
      'Cache-Control': 'no-cache'
    };
  }

  /**
   * 首页 - 获取推荐视频和分类列表
   */
  async home() {
    try {
      const url = `${this.site}/`;
      const html = await request.get(url, { headers: this.headers });
      const $ = cheerio.load(html);

      // 提取分类 (从导航菜单)
      const categories = [];
      $('.top-menu a[data-role="tab"]').each((i, el) => {
        const name = $(el).find('.linkText-64b3c').text().trim();
        const href = $(el).attr('href');
        if (name && href && !name.includes('登入') && !name.includes('注册')) {
          categories.push({
            name: name,
            url: href.startsWith('http') ? href : `${this.site}${href}`
          });
        }
      });

      // 提取推荐视频 (从首页视频卡片)
      const videos = [];
      $('[data-role="video-thumb"], .video-thumb, [data-video-id]').each((i, el) => {
        const title = $(el).find('.video-title, h3, h4, [data-role="video-title"]').text().trim();
        const cover = $(el).find('img').attr('src') || $(el).find('img').attr('data-src');
        const href = $(el).find('a').attr('href');
        const duration = $(el).find('.duration, [data-role="duration"]').text().trim();
        const views = $(el).find('.views, [data-role="views"]').text().trim();

        if (title && href) {
          videos.push({
            title: title,
            cover: cover || '',
            url: href.startsWith('http') ? href : `${this.site}${href}`,
            duration: duration,
            views: views
          });
        }
      });

      // 去重分类名称
      const uniqueCategories = [];
      const seenNames = new Set();
      categories.forEach(cat => {
        if (!seenNames.has(cat.name)) {
          seenNames.add(cat.name);
          uniqueCategories.push(cat);
        }
      });

      return {
        categories: uniqueCategories.map(c => c.name),
        categoryUrls: uniqueCategories.reduce((acc, c, i) => {
          acc[i] = c.url;
          return acc;
        }, {}),
        videos: videos.slice(0, 20) // 首页只返回前20个
      };
    } catch (error) {
      console.error('home error:', error);
      return { categories: [], videos: [] };
    }
  }

  /**
   * 分类 - 获取分类下的视频列表
   * @param {string} url - 分类 URL
   * @param {number} page - 页码 (从1开始)
   */
  async category(url, page = 1) {
    try {
      // 处理分页 URL
      let finalUrl = url;
      if (page > 1) {
        if (url.includes('/page/')) {
          finalUrl = url.replace(/\/page\/\d+/, `/page/${page}`);
        } else {
          finalUrl = `${url}/page/${page}`;
        }
      }

      const html = await request.get(finalUrl, { headers: this.headers });
      const $ = cheerio.load(html);
      const videos = [];

      // 提取视频列表
[2026/5/8 15:39] Leo openclaw qw: $('[data-role="video-thumb"], .video-thumb, [data-video-id]').each((i, el) => {
        const title = $(el).find('.video-title, h3, h4, [data-role="video-title"]').text().trim();
        const cover = $(el).find('img').attr('src') || $(el).find('img').attr('data-src');
        const href = $(el).find('a').attr('href');
        const duration = $(el).find('.duration, [data-role="duration"]').text().trim();
        const views = $(el).find('.views, [data-role="views"]').text().trim();

        if (title && href) {
          videos.push({
            title: title,
            cover: cover || '',
            url: href.startsWith('http') ? href : `${this.site}${href}`,
            duration: duration,
            views: views
          });
        }
      });

      // 检查是否有下一页
      const hasNext = $('.pagination .next, .pagination a:contains("下一页"), [data-role="pagination-next"]').length > 0;

      return {
        videos: videos,
        hasNext: hasNext,
        page: page
      };
    } catch (error) {
      console.error('category error:', error);
      return { videos: [], hasNext: false };
    }
  }

  /**
   * 搜索
   * @param {string} keyword - 搜索关键词
   * @param {number} page - 页码
   */
  async search(keyword, page = 1) {
    try {
      let searchUrl = `${this.site}/search/${encodeURIComponent(keyword)}`;
      if (page > 1) {
        searchUrl += `/page/${page}`;
      }

      const html = await request.get(searchUrl, { headers: this.headers });
      const $ = cheerio.load(html);
      const videos = [];

      // 提取搜索结果
      $('[data-role="video-thumb"], .video-thumb, [data-video-id]').each((i, el) => {
        const title = $(el).find('.video-title, h3, h4, [data-role="video-title"]').text().trim();
        const cover = $(el).find('img').attr('src') || $(el).find('img').attr('data-src');
        const href = $(el).find('a').attr('href');
        const duration = $(el).find('.duration, [data-role="duration"]').text().trim();
        const views = $(el).find('.views, [data-role="views"]').text().trim();

        if (title && href) {
          videos.push({
            title: title,
            cover: cover || '',
            url: href.startsWith('http') ? href : `${this.site}${href}`,
            duration: duration,
            views: views
          });
        }
      });

      const hasNext = $('.pagination .next, .pagination a:contains("下一页"), [data-role="pagination-next"]').length > 0;

      return {
        videos: videos,
        hasNext: hasNext,
        page: page
      };
    } catch (error) {
      console.error('search error:', error);
      return { videos: [], hasNext: false };
    }
  }

  /**
   * 详情 - 获取视频详细信息
   * @param {string} url - 视频 URL
   */
  async detail(url) {
    try {
      const html = await request.get(url, { headers: this.headers });
      const $ = cheerio.load(html);

      // 提取视频信息
      const title = $('h1.video-title, [data-role="video-title"], .video-page-video__title').text().trim();
      const cover = $('meta[property="og:image"]').attr('content') || 
                   $('.video-thumb img').attr('src') || 
                   $('.video-player').find('img').attr('src') || '';
      
      const description = $('meta[name="description"]').attr('content') || 
                         $('.video-description').text().trim() || '';
      
      const duration = $('[data-role="duration"], .video-duration, .duration').text().trim();
      const views = $('[data-role="views"], .video-views, .views').text().trim();
      const rating = $('[data-role="rating"], .video-rating, .rating').text().trim();

      // 提取标签
      const tags = [];
      $('[data-role="tag"], .video-tags a, .tags a').each((i, el) => {
        const tagText = $(el).text().trim();
        if (tagText && !tags.includes(tagText)) {
          tags.push(tagText);
        }
      });

      // 提取上传者信息
[2026/5/8 15:39] Leo openclaw qw:       const uploader = $('[data-role="uploader"], .video-uploader a, .username').text().trim();
[2026/5/8 15:39] Leo openclaw qw: const uploaderUrl = $('[data-role="uploader"], .video-uploader a, .username').attr('href');

      return {
        title: title,
        cover: cover,
        description: description,
        duration: duration,
        views: views,
        rating: rating,
        tags: tags,
        uploader: uploader,
        uploaderUrl: uploaderUrl ? (uploaderUrl.startsWith('http') ? uploaderUrl : `${this.site}${uploaderUrl}`) : '',
        url: url
      };
    } catch (error) {
      console.error('detail error:', error);
      return null;
    }
  }

  /**
   * 播放 - 提取播放地址
   * @param {string} url - 视频 URL
   */
  async play(url) {
    try {
      const html = await request.get(url, { headers: this.headers });
      
      // 尝试多种方法提取播放地址
      let playUrl = '';

      // 方法1: 查找 videoObject JSON 数据
      const videoObjectMatch = html.match(/var\s+videoObject\s*=\s*({[\s\S]*?});/);
      if (videoObjectMatch) {
        try {
          const videoData = JSON.parse(videoObjectMatch[1]);
          if (videoData.sources && Array.isArray(videoData.sources) && videoData.sources.length > 0) {
            // 优先选择最高清晰度
            const sortedSources = videoData.sources.sort((a, b) => {
              const heightA = a.height || 0;
              const heightB = b.height || 0;
              return heightB - heightA;
            });
            playUrl = sortedSources[0].file || sortedSources[0].src;
          }
        } catch (e) {
          // JSON 解析失败，继续尝试其他方法
        }
      }

      // 方法2: 查找 data-hq, data-1080p, data-480p 等属性
      if (!playUrl) {
        const dataHq = $('[data-hq]').attr('data-hq');
        const data1080p = $('[data-1080p]').attr('data-1080p');
        const data720p = $('[data-720p]').attr('data-720p');
        const data480p = $('[data-480p]').attr('data-480p');
        
        if (data1080p) playUrl = data1080p;
        else if (data720p) playUrl = data720p;
        else if (dataHq) playUrl = dataHq;
        else if (data480p) playUrl = data480p;
      }

      // 方法3: 正则匹配 m3u8 或 mp4 链接
      if (!playUrl) {
        const m3u8Match = html.match(/["'](https?:\/\/[^"']*\.m3u8[^"']*)["']/);
        const mp4Match = html.match(/["'](https?:\/\/[^"']*\.mp4[^"']*)["']/);
        
        if (m3u8Match) playUrl = m3u8Match[1];
        else if (mp4Match) playUrl = mp4Match[1];
      }

      // 方法4: 查找 video source 标签
      if (!playUrl) {
        const videoSrc = $('video source').attr('src');
        if (videoSrc) playUrl = videoSrc;
      }

      if (!playUrl) {
        return {
          error: '无法提取播放地址，该视频可能需要登录或已删除',
          url: url
        };
      }

      return {
        url: playUrl,
        headers: this.headers
      };
    } catch (error) {
      console.error('play error:', error);
      return {
        error: '播放地址提取失败',
        url: url
      };
    }
  }
}

// 导出蜘蛛实例
module.exports = new XHamsterSpider();
