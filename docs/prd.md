# DeepShield - Product Requirements Document

## 1. Application Overview

### 1.1 Application Name

DeepShield

### 1.2 Application Description

DeepShield is a web-based digital content analysis platform designed to examine potentially synthetic, manipulated, or AI-generated content.

The platform supports seven analysis categories:

1. Image analysis
2. Video analysis
3. Audio analysis
4. Text analysis
5. Source code analysis
6. Embedding-based analysis
7. Watermark and provenance analysis

Each category operates through its own analysis workflow. Results are presented through a unified interface, with supporting indicators, available measurements, and relevant limitations.

The platform is intended to assist digital content examination. Its findings should be treated as forensic indicators rather than unquestionable proof of authenticity or manipulation.

## 2. Users and Use Cases

### 2.1 Target Users

- Digital forensic investigators.
- Software developers and code reviewers.
- Security and content moderation teams.
- Researchers studying synthetic media.
- Organizations examining digital content provenance.

### 2.2 Core Use Cases

- Submit images, videos, audio, and text for analysis.
- Examine source code for patterns associated with generated or copied code.
- Inspect embedding representations and compare them with supported reference data.
- Examine available watermark signals and content provenance metadata.
- Review analysis results and supporting evidence.
- Save and revisit previous analysis records.
- Switch between light and dark themes.

## 3. Application Structure

```text
DeepShield
│
├── Global Navigation
│   ├── Home
│   ├── Detection
│   ├── History
│   └── Theme Toggle
│
├── Home Page
│
├── Detection Page
│   ├── Image Analysis
│   ├── Video Analysis
│   ├── Audio Analysis
│   ├── Text Analysis
│   ├── Code Analysis
│   ├── Embedding Analysis
│   └── Watermark & Provenance Analysis
│
├── Results Page
│
└── History Page
```

## 4. Functional Requirements

### 4.1 Global Navigation

The application must provide:

- Navigation to Home, Detection, and History.
- Consistent branding across pages.
- A theme toggle for Light and Dark modes.
- Theme persistence across navigation and page reloads.

The interface should not display unnecessary version labels or decorative status badges.

### 4.2 Home Page

The Home Page must:

- Introduce the purpose of DeepShield.
- Explain the available analysis categories.
- Provide direct access to each analysis workflow.
- Include a clear action to start an analysis.
- Provide access to previous analysis records.

Descriptions must reflect the capabilities actually available in the application.

### 4.3 Detection Page

The Detection Page must provide separate workflows for each supported analysis category.

#### 4.3.1 Image Analysis

Input methods:
- Image file upload.
- Image URL, where supported.

Requirements:
- Validate the input format and file size.
- Submit the image to the image analysis module.
- Display processing status.
- Return the available analysis results and indicators.

#### 4.3.2 Video Analysis

Input methods:
- Video file upload.
- Video URL, where supported.

Requirements:
- Validate the file format and size.
- Process the video using the configured analysis pipeline.
- Support frame-based or temporal analysis where implemented.
- Display processing status and available results.

#### 4.3.3 Audio Analysis

Input methods:
- Audio file upload.
- Audio URL, where supported.

Requirements:
- Validate the audio format and size.
- Submit the audio to the configured analysis pipeline.
- Support relevant acoustic or spectral analysis where implemented.
- Display processing status and available results.

#### 4.3.4 Text Analysis

Input methods:
- Direct text entry.
- Text file upload, where supported.

Requirements:
- Reject empty submissions.
- Apply input-length limits.
- Submit text to the configured analysis module.
- Display available statistical or linguistic indicators.
- Explain that text-based authorship detection is probabilistic and can produce false positives.

#### 4.3.5 Code Analysis

Input methods:
- Source code file upload.
- Direct code entry.

Supported file extensions may include `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.cpp`, `.c`, `.java`, `.go`, and other explicitly supported formats.

Requirements:
- Validate the file type and input size.
- Allow the user to specify or select a programming language.
- Use language-aware parsing where supported.
- Examine available indicators such as token patterns, structural regularity, code repetition, and formatting consistency.
- Display metrics only when the corresponding analysis has been performed.

The application must not treat a single coding style, short code sample, or high regularity score as proof of AI authorship.

#### 4.3.6 Embedding Analysis

Input methods:
- Supported media file upload.
- Text input.
- Precomputed embedding input, where supported.

Requirements:
- Extract or accept a compatible representation.
- Use a configured embedding model.
- Compare the representation against an available reference set when one exists.
- Display relevant measurements, such as cosine similarity or distance.
- Identify the reference model and comparison dataset used.

An embedding similarity score must not be presented as a definitive authorship result. Its meaning depends on the model, reference data, and comparison method.

#### 4.3.7 Watermark and Provenance Analysis

Input methods:
- Supported image, audio, video, or document upload.
- URL input, where supported.

Requirements:
- Inspect available metadata.
- Check for supported watermark signals.
- Inspect C2PA Content Credentials when present.
- Report whether a manifest was found and whether its available validation checks succeeded.
- Display unavailable, unsupported, malformed, or invalid metadata distinctly.

The application must not claim to detect every invisible watermark. Support for individual watermark technologies must be explicitly implemented and documented.

A missing watermark or provenance manifest does not prove that content is authentic or synthetic.

## 5. Results Page

The Results Page must display:

### 5.1 Overall Analysis Summary

- Analysis category.
- Submitted file or content preview, where appropriate.
- Overall result or assessment.
- Confidence score, only when provided by a calibrated analysis method.
- Processing status and completion time.

Possible assessment labels:

- Likely synthetic or manipulated.
- No strong synthetic indicators detected.
- Inconclusive.
- Analysis unavailable or incomplete.

The wording must match the actual output of the analysis module.

### 5.2 Supporting Evidence

Display relevant evidence based on the selected analysis category.

**Media Analysis**
- Visual, temporal, acoustic, or other supported indicators.
- Relevant frame or segment references, where available.
- Measurements returned by the configured detector.

**Text Analysis**
- Statistical indicators.
- Repetition and structural patterns.
- Model or classifier output, if available.

**Code Analysis**
- Structural and token-level measurements.
- Repetition and boilerplate indicators.
- Language parsing status.
- Other implemented code-analysis metrics.

**Embedding Analysis**
- Embedding model used.
- Reference dataset or comparison group.
- Similarity and distance measurements.
- Comparison limitations.

**Watermark and Provenance Analysis**
- Supported watermark checks.
- Manifest presence and validation status.
- Available metadata.
- Provenance information and validation limitations.

### 5.3 Result Actions

Users must be able to:

- Save completed analysis records to History.
- Start a new analysis.
- Return to the Detection Page.
- Review the available evidence.

## 6. History Page

The History Page must display saved analysis records in chronological order.

Each record should include:

- Analysis category.
- File name or content description, where available.
- Result or assessment.
- Confidence score, when available.
- Key analysis indicators.
- Submission timestamp.

Users must be able to:

- Open a record to view its detailed results.
- Delete an individual record.
- Navigate through multiple pages of records.

The application should provide appropriate empty, loading, and error states.

## 7. Business Rules and Processing Logic

### 7.1 Theme Management

- Dark mode is the default theme.
- Light mode is available through the navigation toggle.
- Theme changes apply consistently across all pages and components.
- The selected preference persists between sessions.
- System theme preference may be used when no saved preference exists.

### 7.2 Analysis Workflow

1. The user selects an analysis category.
2. The user supplies a file, URL, or text input supported by that category.
3. The application validates the input.
4. The request is sent to the corresponding analysis module.
5. The module processes the input using its configured method.
6. The module returns its result, supporting indicators, and any relevant warnings.
7. The Results Page displays the returned information.
8. The completed result can be saved to History.

Each analysis category must have an independent processing workflow. A failure in one category should not be represented as a successful result from another category.

### 7.3 Result and Confidence Interpretation

- Confidence values must come from the configured model or analysis method.
- Confidence values must be constrained to the documented range.
- Scores from different analysis categories must not be treated as directly interchangeable.
- A score must not automatically determine authenticity unless the underlying model has been evaluated and calibrated for that interpretation.
- Missing measurements must be shown as unavailable, not fabricated or replaced with zero.
- Conflicting indicators should be reported rather than hidden by an arbitrary overall score.

Watermark and provenance results must be displayed separately from model-based synthetic-content predictions. A valid provenance manifest can provide evidence about a file's origin or editing history, but it does not automatically establish that the content is truthful.

## 8. Exceptions and Boundary Cases

| Scenario | Expected handling |
|---|---|
| Unsupported file format | Display an unsupported-format message |
| Empty text or code input | Reject the submission and request valid input |
| File exceeds size limit | Display the configured size limit |
| Unreadable or corrupted file | Report that the file could not be processed |
| Unsupported programming language | Explain which analysis methods remain available |
| Invalid URL | Display a URL validation error |
| Missing watermark | Report that no supported watermark was detected |
| Missing C2PA manifest | Report that no manifest was found |
| Malformed provenance metadata | Report an invalid or unreadable manifest |
| Analysis service unavailable | Display an error and allow retry |
| Partial analysis failure | Show completed checks and identify unavailable checks |
| No history records | Display an appropriate empty state |

## 9. Acceptance Criteria

The application is considered to meet its core requirements when:

1. Users can navigate between Home, Detection, and History.
2. Users can switch between Light and Dark themes.
3. Theme preferences persist after page reloads.
4. All seven analysis categories are accessible.
5. Each category validates its own supported input types.
6. Each category submits requests to its corresponding processing module.
7. Results reflect actual module responses rather than placeholder or randomly generated values.
8. The Results Page displays relevant evidence and clearly identifies unavailable measurements.
9. Users can save completed analysis records.
10. Saved records can be viewed and deleted through History.
11. Errors and incomplete analyses are communicated clearly.
12. The interface remains usable on desktop and smaller screens.

## 10. Features Outside the Current Release

The following features are not required for the current release:

- Automated repository scanning through CI/CD pipelines.
- Automated legal filing or takedown requests.
- User authentication and role-based access control.
- Public API billing and rate limiting.
- Large-scale batch processing.
- Guaranteed detection of all AI-generated content.
- Universal support for every proprietary watermark technology.
- Definitive identification of the person or system that created a file.

These features may be considered separately in future development.