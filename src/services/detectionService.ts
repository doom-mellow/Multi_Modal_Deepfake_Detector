import type { DetectionRequest, DetectionResult, MediaType } from '@/types/types';

/**
 * Mock AI detection service that simulates forensic analysis
 * Based on research report findings for text, audio, and video detection
 */

// Simulate processing delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Generate realistic confidence scores with some randomness
function generateConfidence(baseConfidence: number): number {
  const variance = Math.random() * 20 - 10; // ±10% variance
  return Math.max(0, Math.min(100, Math.round(baseConfidence + variance)));
}

// Image detection based on GAN artifacts and manipulation traces
// Includes advanced deepfake detection for face-swapped content
function detectImage(fileName: string): DetectionResult {
  // Simulate comprehensive image forensic analysis including deepfake detection
  const hasGANArtifacts = Math.random() > 0.5;
  const hasLightingInconsistencies = Math.random() > 0.4;
  const hasCompressionAnomalies = Math.random() > 0.3;
  const hasEdgeArtifacts = Math.random() > 0.4;
  const hasColorAnomalies = Math.random() > 0.3;
  
  // Advanced deepfake-specific checks
  const hasFaceSwapArtifacts = Math.random() > 0.45;
  const hasFacialBoundaryAnomalies = Math.random() > 0.4;
  const hasSkinToneInconsistencies = Math.random() > 0.35;
  const hasDeepfakeSignature = Math.random() > 0.4;
  
  let confidence = 35;
  if (hasGANArtifacts) confidence += 20;
  if (hasLightingInconsistencies) confidence += 12;
  if (hasCompressionAnomalies) confidence += 8;
  if (hasEdgeArtifacts) confidence += 10;
  if (hasFaceSwapArtifacts) confidence += 15;
  if (hasFacialBoundaryAnomalies) confidence += 12;
  if (hasSkinToneInconsistencies) confidence += 10;
  if (hasDeepfakeSignature) confidence += 13;
  
  confidence = generateConfidence(confidence);
  const isAI = confidence > 50;
  
  const indicators: string[] = [];
  if (hasGANArtifacts) indicators.push('GAN fingerprint patterns detected in frequency domain');
  if (hasLightingInconsistencies) indicators.push('Inconsistent lighting and shadow directions');
  if (hasCompressionAnomalies) indicators.push('Unusual JPEG compression artifacts');
  if (hasEdgeArtifacts) indicators.push('Unnatural edge transitions and blending');
  if (hasColorAnomalies) indicators.push('Color distribution anomalies detected');
  if (hasFaceSwapArtifacts) indicators.push('Face-swap artifacts detected at facial boundaries');
  if (hasFacialBoundaryAnomalies) indicators.push('Unnatural transitions between face and surrounding areas');
  if (hasSkinToneInconsistencies) indicators.push('Skin tone and texture inconsistencies detected');
  if (hasDeepfakeSignature) indicators.push('Deepfake neural network signature patterns identified');
  if (!hasGANArtifacts && !hasEdgeArtifacts && !hasFaceSwapArtifacts) {
    indicators.push('Natural noise patterns consistent with camera sensors');
  }
  
  return {
    result: isAI ? 'ai-generated' : 'real',
    confidence: isAI ? confidence : 100 - confidence,
    explanation: isAI
      ? 'Analysis reveals AI-specific artifacts, manipulation patterns, and synthetic characteristics. Detected anomalies include GAN signatures, lighting inconsistencies, and potential face-swapping indicators.'
      : 'Image exhibits natural camera noise, consistent lighting, and authentic compression patterns typical of real photographs. No evidence of AI manipulation detected.',
    indicators
  };
}

// Text detection based on perplexity and burstiness analysis
function detectText(content: string): DetectionResult {
  const wordCount = content.split(/\s+/).length;
  const avgWordLength = content.length / wordCount;
  const sentenceCount = content.split(/[.!?]+/).length;
  const avgSentenceLength = wordCount / sentenceCount;
  
  // Heuristics: AI text tends to have uniform structure
  const uniformity = Math.abs(avgSentenceLength - 15) < 5 && avgWordLength > 4.5;
  const hasGenericPhrases = /\b(it is important to note|in conclusion|furthermore|moreover)\b/i.test(content);
  
  let confidence = 50;
  if (uniformity) confidence += 20;
  if (hasGenericPhrases) confidence += 15;
  if (wordCount < 50) confidence -= 10; // Short text is harder to detect
  
  confidence = generateConfidence(confidence);
  const isAI = confidence > 50;
  
  const indicators: string[] = [];
  if (uniformity) indicators.push('Uniform sentence structure detected');
  if (hasGenericPhrases) indicators.push('Generic AI phrases identified');
  if (avgWordLength > 5) indicators.push('High vocabulary complexity');
  
  return {
    result: isAI ? 'ai-generated' : 'real',
    confidence: isAI ? confidence : 100 - confidence,
    explanation: isAI 
      ? 'Statistical analysis indicates low perplexity and uniform burstiness patterns typical of LLM-generated content.'
      : 'Text exhibits natural irregularity and personal writing patterns consistent with human authorship.',
    indicators
  };
}

// Audio detection based on spectral analysis and prosody
function detectAudio(fileName: string): DetectionResult {
  // Simulate spectral analysis
  const hasCleanSpectrum = Math.random() > 0.5;
  const lacksProsody = Math.random() > 0.4;
  const hasArtifacts = Math.random() > 0.3;
  
  let confidence = 45;
  if (hasCleanSpectrum) confidence += 25;
  if (lacksProsody) confidence += 20;
  if (hasArtifacts) confidence += 10;
  
  confidence = generateConfidence(confidence);
  const isAI = confidence > 50;
  
  const indicators: string[] = [];
  if (hasCleanSpectrum) indicators.push('Unnaturally clean high-frequency spectrum');
  if (lacksProsody) indicators.push('Lack of natural emotional micro-variations');
  if (hasArtifacts) indicators.push('Digital synthesis artifacts detected');
  if (!lacksProsody) indicators.push('Natural breathing sounds present');
  
  return {
    result: isAI ? 'ai-generated' : 'real',
    confidence: isAI ? confidence : 100 - confidence,
    explanation: isAI
      ? 'Spectral analysis reveals anomalies and lack of natural prosody typical of neural TTS systems.'
      : 'Audio contains natural imperfections, breathing patterns, and emotional variations consistent with human speech.',
    indicators
  };
}

// Video detection based on biological signals and temporal consistency
function detectVideo(fileName: string): DetectionResult {
  // Simulate deepfake detection
  const hasBlinkingAnomalies = Math.random() > 0.6;
  const hasLightingInconsistencies = Math.random() > 0.5;
  const hasEdgeArtifacts = Math.random() > 0.4;
  const hasTemporalJitter = Math.random() > 0.3;
  
  let confidence = 40;
  if (hasBlinkingAnomalies) confidence += 20;
  if (hasLightingInconsistencies) confidence += 15;
  if (hasEdgeArtifacts) confidence += 15;
  if (hasTemporalJitter) confidence += 10;
  
  confidence = generateConfidence(confidence);
  const isAI = confidence > 50;
  
  const indicators: string[] = [];
  if (hasBlinkingAnomalies) indicators.push('Unnatural eye blinking patterns detected');
  if (hasLightingInconsistencies) indicators.push('Lighting and shadow inconsistencies found');
  if (hasEdgeArtifacts) indicators.push('Edge artifacts around facial boundaries');
  if (hasTemporalJitter) indicators.push('Temporal jitter between frames');
  if (!hasBlinkingAnomalies) indicators.push('Natural biological signals present');
  
  return {
    result: isAI ? 'ai-generated' : 'real',
    confidence: isAI ? confidence : 100 - confidence,
    explanation: isAI
      ? 'Analysis reveals biological signal anomalies and temporal inconsistencies characteristic of GAN-generated video.'
      : 'Video exhibits natural biological signals, consistent lighting, and temporal coherence typical of authentic footage.',
    indicators
  };
}

/**
 * Main detection function that routes to appropriate detection method
 */
export async function performDetection(request: DetectionRequest): Promise<DetectionResult> {
  // Simulate processing time (1-3 seconds)
  await delay(1000 + Math.random() * 2000);
  
  switch (request.mediaType) {
    case 'image':
      if (!request.file && !request.url) {
        throw new Error('Image file or URL is required');
      }
      return detectImage(request.file?.name || request.url || 'image');
      
    case 'text':
      if (!request.content) {
        throw new Error('Text content is required');
      }
      return detectText(request.content);
      
    case 'audio':
      if (!request.file) {
        throw new Error('Audio file is required');
      }
      return detectAudio(request.file.name);
      
    case 'video':
      if (!request.file && !request.url) {
        throw new Error('Video file or URL is required');
      }
      return detectVideo(request.file?.name || request.url || 'video');
      
    default:
      throw new Error('Unsupported media type');
  }
}

/**
 * Validate file size and format
 */
export function validateFile(file: File, mediaType: MediaType): { valid: boolean; error?: string } {
  const maxSize = 100 * 1024 * 1024; // 100MB
  
  if (file.size > maxSize) {
    return { valid: false, error: 'File too large, maximum size is 100MB' };
  }
  
  const validFormats: Record<MediaType, string[]> = {
    image: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'],
    video: ['video/mp4', 'video/avi', 'video/quicktime', 'video/webm'],
    audio: ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/ogg'],
    text: ['text/plain']
  };
  
  if (!validFormats[mediaType].includes(file.type)) {
    return { valid: false, error: 'Unsupported format, please upload valid file' };
  }
  
  return { valid: true };
}

/**
 * Validate URL format
 */
export function validateUrl(url: string): { valid: boolean; error?: string } {
  try {
    new URL(url);
    return { valid: true };
  } catch {
    return { valid: false, error: 'Invalid URL, please check and resubmit' };
  }
}
