# DeepShield AI

**A Multimodal Digital Forensics Platform for AI-Generated and Manipulated Content**

DeepShield AI is a web-based platform designed to support the forensic examination of digital content. It provides an organized interface for submitting content, reviewing analysis results, and maintaining detection history.

The platform is structured around seven analysis categories:

1. Image analysis
2. Video analysis
3. Audio analysis
4. Text analysis
5. Code analysis
6. Embedding analysis
7. Watermark and provenance analysis

> **Development note:** The availability of an analysis category in the interface does not mean its detector is operational. Each category requires an appropriate analysis implementation or model integration before it can produce genuine detection results.

## Technology Stack

| Area | Technology |
|---|---|
| Frontend | React, TypeScript |
| Development and build | Vite |
| Styling | Tailwind CSS |
| UI components | Radix UI |
| Backend services | Supabase |
| Database | PostgreSQL |
| Authentication | Supabase Auth |
| Routing | React Router |

## Project Structure

```text
deepfake_detetctor/
├── public/
├── src/
│   ├── components/
│   │   ├── common/
│   │   └── ui/
│   ├── contexts/
│   ├── db/
│   ├── hooks/
│   ├── pages/
│   ├── services/
│   ├── types/
│   ├── lib/
│   ├── App.tsx
│   ├── index.css
│   ├── main.tsx
│   └── routes.tsx
├── supabase/
│   └── migrations/
├── tasks/
├── .env.example
├── .gitignore
├── index.html
├── package.json
├── package-lock.json
└── vite.config.ts
```

## Requirements

- Node.js compatible with the installed Vite version
- npm
- A Supabase project

## Local Setup

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd deepfake_detetctor
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment variables

Create a `.env` file in the project root.

```env
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_publishable_key
```

If username-based authentication is required, optionally configure:

```env
VITE_AUTH_EMAIL_DOMAIN=your_authentication_domain
```

Users can alternatively authenticate using their actual email addresses.

Use the Supabase publishable key for frontend access. Never expose a Supabase secret key or service-role key in frontend environment variables.

### 4. Start the development server

```bash
npm run dev
```

### 5. Run the TypeScript check

```bash
npm run typecheck
```

### 6. Create a production build

```bash
npm run build
```

### 7. Preview the production build

```bash
npm run preview
```

## Supabase Configuration

DeepShield AI uses Supabase for authentication and database operations.

Database migrations are stored in:

```text
supabase/migrations/
```

Apply the migrations to your Supabase project before using database-dependent functionality.

The `detection_history` table supports all seven analysis categories and stores associated result metadata.

Row Level Security policies restrict authenticated users to their own detection history.

## Current Development Status

DeepShield AI is being developed in stages.

The frontend provides the interface and structure for the seven analysis categories. Supabase provides authentication and database functionality, including detection history management.

The actual AI inference process is a separate development component. Each detector requires an appropriate model, analysis implementation, or external service integration before it can return genuine results.

The platform is intended to communicate uncertainty and limitations clearly. Heuristic scores, unavailable detectors, and missing provenance information must not be presented as conclusive evidence.

## Project Goals

- Support multiple digital content types.
- Integrate appropriate detection approaches for each modality.
- Present analysis results with understandable explanations.
- Maintain detection history securely.
- Communicate uncertainty and technical limitations clearly.
- Provide a simple and accessible interface for digital forensic analysis.
