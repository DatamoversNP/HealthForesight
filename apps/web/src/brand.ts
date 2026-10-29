/** Product chrome. Defaults keep the HealthForesight build unchanged. */
export const appName = import.meta.env.VITE_APP_NAME || 'HealthForesight'
export const appByline = import.meta.env.VITE_APP_BYLINE ?? 'by DataMovers'
export const logoSrc = import.meta.env.VITE_LOGO_SRC || '/healthforesight-logo.svg'
export const logoIconSrc = import.meta.env.VITE_LOGO_ICON_SRC || '/healthforesight-logo-icon.svg'
export const logoOnDarkSrc = import.meta.env.VITE_LOGO_ON_DARK_SRC || ''
export const faviconSrc = import.meta.env.VITE_FAVICON || ''
export const appBarFullLogo = import.meta.env.VITE_APP_BAR_FULL_LOGO === 'true'

export const documentTitle = `${appName} - Decision Intelligence for Utilization Policy Impact`

export function applyDocumentBrand() {
  document.title = documentTitle
  if (!faviconSrc) return
  let link = document.querySelector<HTMLLinkElement>("link[rel='icon']")
  if (!link) {
    link = document.createElement('link')
    link.rel = 'icon'
    document.head.appendChild(link)
  }
  link.type = 'image/png'
  link.href = faviconSrc
}
