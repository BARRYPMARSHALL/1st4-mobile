import type { MetadataRoute } from 'next'

const BASE_URL = 'https://app.1st4.mobi'

export default function sitemap(): MetadataRoute.Sitemap {
  const today = new Date('2026-06-11')

  return [
    // Static / Content Pages (priority 0.8)
    {
      url: BASE_URL,
      lastModified: today,
      changeFrequency: 'monthly',
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/blog`,
      lastModified: today,
      changeFrequency: 'weekly',
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/book`,
      lastModified: today,
      changeFrequency: 'monthly',
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/privacy`,
      lastModified: today,
      changeFrequency: 'monthly',
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/terms`,
      lastModified: today,
      changeFrequency: 'monthly',
      priority: 0.8,
    },

    // Blog Posts (priority 0.6)
    {
      url: `${BASE_URL}/blog/why-corporate-mobile-bill-wrong`,
      lastModified: today,
      changeFrequency: 'weekly',
      priority: 0.6,
    },
    {
      url: `${BASE_URL}/blog/45k-hidden-overcharges`,
      lastModified: today,
      changeFrequency: 'weekly',
      priority: 0.6,
    },
    {
      url: `${BASE_URL}/blog/5-billing-errors-telstra-hides`,
      lastModified: today,
      changeFrequency: 'weekly',
      priority: 0.6,
    },
    {
      url: `${BASE_URL}/blog/dispute-telco-bill-win`,
      lastModified: today,
      changeFrequency: 'weekly',
      priority: 0.6,
    },

    // Auth / Utility Pages (priority 0.3)
    {
      url: `${BASE_URL}/login`,
      lastModified: today,
      changeFrequency: 'monthly',
      priority: 0.3,
    },
    {
      url: `${BASE_URL}/register`,
      lastModified: today,
      changeFrequency: 'monthly',
      priority: 0.3,
    },
    {
      url: `${BASE_URL}/portal`,
      lastModified: today,
      changeFrequency: 'monthly',
      priority: 0.3,
    },
  ]
}
