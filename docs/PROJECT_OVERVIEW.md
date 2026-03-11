# 프로젝트 개요

이 문서는 팀원이 프로젝트의 기본 기술 스택과 저장소 구조를 빠르게 이해할 수 있도록 정리한 문서입니다.

## 기술 스택

- Frontend: Next.js
- Backend: NestJS
- Database: PostgreSQL
- ORM: Prisma
- Monorepo package manager: pnpm workspace

## 저장소 전략

- 이 프로젝트는 모노레포 구조를 사용한다.
- 애플리케이션은 `apps/` 아래에서 관리한다.
- 공통 타입, 스키마, 유틸리티는 `packages/shared/`에서 관리한다.

## 모노레포 구조

```text
repo/
  apps/
    web/         # Next.js frontend
    api/         # NestJS backend
  packages/
    shared/      # shared types, schemas, utilities
  package.json
  pnpm-workspace.yaml
```
