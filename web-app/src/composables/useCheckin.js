import { ref } from 'vue'
import { copyToClipboard, useQuasar } from 'quasar'

export function useCheckin() {
  const $q = useQuasar()
  const qrDialogOpen = ref(false)
  const qrUrl = ref('')

  function getMagicLink(order) {
    if (!order) return ''
    const id = typeof order === 'object' ? order.id : order
    if (!id) return ''
    const baseUrl = window.location.origin + window.location.pathname
    return `${baseUrl}#/consenso?order_id=${id}`
  }

  function copyMagicLink(order) {
    const link = getMagicLink(order)
    if (!link) return
    copyToClipboard(link)
      .then(() => {
        if ($q) $q.notify({ message: 'Magic Link copiato negli appunti', color: 'positive', icon: 'check', position: 'top' })
      })
      .catch(() => {
        if ($q) $q.notify({ message: 'Errore durante la copia del link', color: 'negative', icon: 'warning', position: 'top' })
      })
  }

  function openQrModal(order) {
    const link = getMagicLink(order)
    if (!link) return
    qrUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(link)}`
    qrDialogOpen.value = true
  }

  function shareWhatsApp(order) {
    const link = getMagicLink(order)
    if (!link) return
    const customerName = typeof order === 'object' && order.customer_name ? ` ${order.customer_name}` : ''
    const text = `Ciao${customerName},\necco il link per la registrazione della tua discesa: ${link}\n\nCompilalo per tutti i partecipanti prima di arrivare in base.`
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank')
  }

  return { qrDialogOpen, qrUrl, getMagicLink, copyMagicLink, openQrModal, shareWhatsApp }
}
