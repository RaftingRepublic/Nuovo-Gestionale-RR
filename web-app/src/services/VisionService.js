import { api } from 'src/boot/axios'

export default {
  /**
   * Invia i documenti al backend per l'analisi OCR.
   * Prova prima /registration/scan, poi fallback su /vision/analyze (compatibilità).
   */
  async analyzeDocument (frontFile, backFile = null, docType = 'AUTO') {
    const buildFormData = () => {
      const formData = new FormData()
      formData.append('front', frontFile)
      if (backFile) formData.append('back', backFile)

      // Compatibilità con endpoint legacy
      formData.append('use_local', 'true')
      formData.append('doc_type', docType)

      return formData
    }

    const postMultipart = async (url) => {
      const formData = buildFormData()
      return api.post(url, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    }

    try {
      // 1) Endpoint nuovo
      try {
        const res = await postMultipart('/registration/scan')
        const data = res.data
        return (data && typeof data === 'object' && data.extracted) ? data.extracted : data
      } catch (e) {
        const status = e?.response?.status
        if (status !== 404 && status !== 405) throw e
      }

      // 2) Fallback legacy
      const res = await postMultipart('/vision/analyze')
      return res.data
    } catch (error) {
      console.error('VisionService Error:', error)
      if (error?.response?.data?.detail) throw new Error(error.response.data.detail)
      throw new Error('Impossibile connettersi al server di Analisi.')
    }
  }
}
