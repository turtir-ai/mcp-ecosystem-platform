/**
 * Smart Error Handler - AI-powered error analysis and user-friendly messaging
 * 
 * Bu servis, API hatalarını yakalar, AI ile analiz eder ve kullanıcıya
 * anlamlı çözüm önerileri sunar.
 */

import axios, { AxiosError } from 'axios';

// Type Definitions
export interface RequestContext {
  url: string;
  method: string;
  timestamp: Date;
  userAgent: string;
  currentRoute: string;
  userActions: UserAction[];
}

export interface UserAction {
  type: string;
  timestamp: Date;
  details: Record<string, any>;
}

export interface ActionSuggestion {
  title: string;
  description: string;
  actionType: 'manual' | 'ai_assisted' | 'automatic';
  estimatedTime: string;
  riskLevel: 'safe' | 'low' | 'medium' | 'high';
  steps?: string[];
  automationAvailable?: boolean;
}

export interface SmartErrorResponse {
  userFriendlyMessage: string;
  technicalDetails: string;
  suggestedActions: ActionSuggestion[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  canAutoFix: boolean;
  aiAnalysis?: {
    rootCause: string;
    confidence: number;
    similarIssues: number;
    estimatedResolutionTime: string;
  };
}

export interface ErrorAnalysisRequest {
  errorType: string;
  errorMessage: string;
  stackTrace?: string;
  requestContext: RequestContext;
  systemContext: {
    currentRoute: string;
    userActions: UserAction[];
    systemHealth?: any;
  };
}

// Smart Error Handler Class
export class SmartErrorHandler {
  private apiBaseUrl: string;
  private userActionHistory: UserAction[] = [];
  private errorPatterns: Map<string, SmartErrorResponse> = new Map();

  constructor(apiBaseUrl: string = '/api/v1') {
    this.apiBaseUrl = apiBaseUrl;
    this.initializeErrorPatterns();
  }

  /**
   * Ana hata yakalama ve analiz metodu
   */
  async handleError(error: Error, context: Partial<RequestContext> = {}): Promise<SmartErrorResponse> {
    const requestContext = this.buildRequestContext(context);
    
    // Hata tipini belirle
    if (axios.isAxiosError(error)) {
      return this.handleAxiosError(error, requestContext);
    }
    
    // Genel JavaScript hataları
    return this.handleGenericError(error, requestContext);
  }

  /**
   * Axios/HTTP hatalarını işle
   */
  async handleAxiosError(error: AxiosError, context: RequestContext): Promise<SmartErrorResponse> {
    const errorCode = error.code;
    const statusCode = error.response?.status;
    const responseData = error.response?.data as any;

    // Bağlantı hataları
    if (errorCode === 'ERR_NETWORK' || errorCode === 'ERR_CONNECTION_REFUSED') {
      return this.handleConnectionError(error, context);
    }

    // Timeout hataları
    if (errorCode === 'ECONNABORTED' || error.message.includes('timeout')) {
      return this.handleTimeoutError(error, context);
    }

    // Server hataları (5xx)
    if (statusCode && statusCode >= 500) {
      return this.handleServerError(error, context);
    }

    // Client hataları (4xx)
    if (statusCode && statusCode >= 400 && statusCode < 500) {
      return this.handleClientError(error, context);
    }

    // Diğer axios hataları
    return this.handleGenericAxiosError(error, context);
  }

  /**
   * Bağlantı hatalarını AI ile analiz et
   */
  async handleConnectionError(error: AxiosError, context: RequestContext): Promise<SmartErrorResponse> {
    const errorKey = `connection_${error.code}_${context.url}`;
    
    // Cache'den kontrol et
    if (this.errorPatterns.has(errorKey)) {
      return this.errorPatterns.get(errorKey)!;
    }

    try {
      // AI analizi için backend'e gönder
      const aiAnalysis = await this.requestAIAnalysis({
        errorType: 'connection_error',
        errorMessage: error.message,
        requestContext: context,
        systemContext: {
          currentRoute: context.currentRoute,
          userActions: this.userActionHistory.slice(-5) // Son 5 eylem
        }
      });

      const smartResponse: SmartErrorResponse = {
        userFriendlyMessage: aiAnalysis?.userFriendlyMessage || this.getDefaultConnectionMessage(),
        technicalDetails: `${error.code}: ${error.message}`,
        suggestedActions: aiAnalysis?.suggestedActions || this.getDefaultConnectionActions(),
        severity: 'high',
        canAutoFix: false,
        aiAnalysis: aiAnalysis?.analysis
      };

      // Cache'e kaydet
      this.errorPatterns.set(errorKey, smartResponse);
      return smartResponse;

    } catch (aiError) {
      // AI analizi başarısız olursa fallback kullan
      return this.getFallbackConnectionResponse(error, context);
    }
  }

  /**
   * Timeout hatalarını işle
   */
  async handleTimeoutError(error: AxiosError, context: RequestContext): Promise<SmartErrorResponse> {
    return {
      userFriendlyMessage: "İstek zaman aşımına uğradı. Sunucu yavaş yanıt veriyor olabilir.",
      technicalDetails: `Timeout: ${error.message}`,
      suggestedActions: [
        {
          title: "Tekrar Dene",
          description: "İsteği tekrar gönder",
          actionType: 'manual',
          estimatedTime: "Anında",
          riskLevel: 'safe'
        },
        {
          title: "Sistem Durumunu Kontrol Et",
          description: "Backend sunucusunun durumunu kontrol et",
          actionType: 'ai_assisted',
          estimatedTime: "30 saniye",
          riskLevel: 'safe'
        }
      ],
      severity: 'medium',
      canAutoFix: true
    };
  }

  /**
   * Server hatalarını işle
   */
  async handleServerError(error: AxiosError, context: RequestContext): Promise<SmartErrorResponse> {
    const statusCode = error.response?.status;
    
    return {
      userFriendlyMessage: `Sunucu hatası oluştu (${statusCode}). Teknik ekip bilgilendirildi.`,
      technicalDetails: `HTTP ${statusCode}: ${error.message}`,
      suggestedActions: [
        {
          title: "Birkaç Dakika Bekle",
          description: "Sunucu sorunu geçici olabilir",
          actionType: 'manual',
          estimatedTime: "2-5 dakika",
          riskLevel: 'safe'
        },
        {
          title: "Sistem Yöneticisine Bildir",
          description: "Sorun devam ederse destek ekibiyle iletişime geç",
          actionType: 'manual',
          estimatedTime: "5 dakika",
          riskLevel: 'safe'
        }
      ],
      severity: 'high',
      canAutoFix: false
    };
  }

  /**
   * Client hatalarını işle
   */
  async handleClientError(error: AxiosError, context: RequestContext): Promise<SmartErrorResponse> {
    const statusCode = error.response?.status;
    const responseData = error.response?.data as any;

    let message = "İstek hatası oluştu.";
    let actions: ActionSuggestion[] = [];

    switch (statusCode) {
      case 401:
        message = "Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.";
        actions = [{
          title: "Tekrar Giriş Yap",
          description: "Giriş sayfasına yönlendirileceksiniz",
          actionType: 'automatic',
          estimatedTime: "Anında",
          riskLevel: 'safe'
        }];
        break;
      case 403:
        message = "Bu işlem için yetkiniz bulunmuyor.";
        actions = [{
          title: "Yetki Talep Et",
          description: "Sistem yöneticisinden yetki talep edin",
          actionType: 'manual',
          estimatedTime: "Değişken",
          riskLevel: 'safe'
        }];
        break;
      case 404:
        message = "Aradığınız kaynak bulunamadı.";
        actions = [{
          title: "Ana Sayfaya Dön",
          description: "Ana sayfadan tekrar deneyin",
          actionType: 'manual',
          estimatedTime: "Anında",
          riskLevel: 'safe'
        }];
        break;
      default:
        message = responseData?.message || `İstek hatası (${statusCode})`;
    }

    return {
      userFriendlyMessage: message,
      technicalDetails: `HTTP ${statusCode}: ${JSON.stringify(responseData)}`,
      suggestedActions: actions,
      severity: statusCode === 401 ? 'medium' : 'low',
      canAutoFix: statusCode === 401
    };
  }

  /**
   * Genel hataları işle
   */
  async handleGenericError(error: Error, context: RequestContext): Promise<SmartErrorResponse> {
    return {
      userFriendlyMessage: "Beklenmeyen bir hata oluştu. Lütfen sayfayı yenileyin.",
      technicalDetails: `${error.name}: ${error.message}`,
      suggestedActions: [
        {
          title: "Sayfayı Yenile",
          description: "Tarayıcı sayfasını yenileyin",
          actionType: 'manual',
          estimatedTime: "Anında",
          riskLevel: 'safe'
        },
        {
          title: "Tarayıcı Cache'ini Temizle",
          description: "Tarayıcı önbelleğini temizleyin",
          actionType: 'manual',
          estimatedTime: "1 dakika",
          riskLevel: 'safe'
        }
      ],
      severity: 'medium',
      canAutoFix: false
    };
  }

  /**
   * Genel Axios hatalarını işle
   */
  async handleGenericAxiosError(error: AxiosError, context: RequestContext): Promise<SmartErrorResponse> {
    return {
      userFriendlyMessage: "API isteği başarısız oldu. Lütfen tekrar deneyin.",
      technicalDetails: `${error.code}: ${error.message}`,
      suggestedActions: [
        {
          title: "Tekrar Dene",
          description: "İsteği tekrar gönder",
          actionType: 'manual',
          estimatedTime: "Anında",
          riskLevel: 'safe'
        }
      ],
      severity: 'medium',
      canAutoFix: true
    };
  }

  /**
   * AI analizi için backend'e istek gönder
   */
  private async requestAIAnalysis(request: ErrorAnalysisRequest): Promise<any> {
    try {
      const response = await axios.post(`${this.apiBaseUrl}/ai/analyze-error`, request, {
        timeout: 5000 // AI analizi için kısa timeout
      });
      return response.data;
    } catch (error) {
      console.warn('AI error analysis failed:', error);
      return null;
    }
  }

  /**
   * Request context oluştur
   */
  private buildRequestContext(partial: Partial<RequestContext>): RequestContext {
    return {
      url: partial.url || window.location.href,
      method: partial.method || 'GET',
      timestamp: new Date(),
      userAgent: navigator.userAgent,
      currentRoute: partial.currentRoute || window.location.pathname,
      userActions: partial.userActions || this.userActionHistory.slice(-3)
    };
  }

  /**
   * Kullanıcı eylemini kaydet
   */
  trackUserAction(action: UserAction): void {
    this.userActionHistory.push(action);
    
    // Son 50 eylemi tut
    if (this.userActionHistory.length > 50) {
      this.userActionHistory = this.userActionHistory.slice(-50);
    }
  }

  /**
   * Varsayılan hata pattern'lerini başlat
   */
  private initializeErrorPatterns(): void {
    // Yaygın hata pattern'leri için cache
    // Bu, AI analizi yapılamadığında kullanılır
  }

  /**
   * Varsayılan bağlantı mesajı
   */
  private getDefaultConnectionMessage(): string {
    return "Backend sunucusuna bağlanılamıyor. Sunucu çalışmıyor olabilir veya ağ bağlantınızda sorun olabilir.";
  }

  /**
   * Varsayılan bağlantı eylemleri
   */
  private getDefaultConnectionActions(): ActionSuggestion[] {
    return [
      {
        title: "Backend Durumunu Kontrol Et",
        description: "Backend sunucusunun çalışıp çalışmadığını kontrol edin",
        actionType: 'manual',
        estimatedTime: "1 dakika",
        riskLevel: 'safe',
        steps: [
          "Terminal açın",
          "Backend klasörüne gidin",
          "python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 komutunu çalıştırın"
        ]
      },
      {
        title: "Ağ Bağlantısını Kontrol Et",
        description: "İnternet bağlantınızı kontrol edin",
        actionType: 'manual',
        estimatedTime: "30 saniye",
        riskLevel: 'safe'
      }
    ];
  }

  /**
   * Fallback bağlantı yanıtı
   */
  private getFallbackConnectionResponse(error: AxiosError, context: RequestContext): SmartErrorResponse {
    return {
      userFriendlyMessage: this.getDefaultConnectionMessage(),
      technicalDetails: `${error.code}: ${error.message}`,
      suggestedActions: this.getDefaultConnectionActions(),
      severity: 'high',
      canAutoFix: false
    };
  }
}

// Singleton instance
export const smartErrorHandler = new SmartErrorHandler();

// Convenience functions
export const handleError = (error: Error, context?: Partial<RequestContext>) => 
  smartErrorHandler.handleError(error, context);

export const trackUserAction = (action: UserAction) => 
  smartErrorHandler.trackUserAction(action);