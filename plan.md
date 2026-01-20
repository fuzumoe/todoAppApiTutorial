 Todo App
 - what is the app? definition and description
 - who are the users? elaboration
 - what are the activities performed in the app? bc, ac, rc
    - business activities [bc]
    - audit activities [ac]
    - reporting activities
 - scope of the app?


Actors:
 - USER
 - MANAGER
 - ADMIN

Activities:
- USER RELATED ACTIVITIES
   - CREATE USER
   - UPDATE USER
   - DELETE USER
-  PROJECT RELATED ACTIVITIES
   - CREATE PROJECT
   - UPDATE PROJECT
   - DELETE PROJECT
- TASK RELATED ACTIVITIES
   - CREATE TASK
   - UPDATE TASK
   - DELETE TASK
- COMMON [ENUM]
  - CREATE
  - UPDATE 
  - DELETE

ENTITIES:
 - TASK
 - PROJECT

MODEL:
 - USERS [WITH ROLES]
  - ID: [id] .....
  - FULL_NAME: [fullName] ...
  - EMAIL: [email] ....
  - PASSWORD: [password] ....
  - etc ....
  - ROLES: [role:ENUM] ....
    - USER
    - MANAGER
    - ADMIN
  - CREATED_AT: [createdAt:datetime]
  - UPDATED_AT: [updatedAt:datetime]
  - IS_ACTIVE: [isActive:boolean] 
 - TASK
  - ID: [id] .....
  - DESCRIPTION: [description]
  - PROJECT_ID: [projectId:foreignKey]
  - ASSIGNED_TO: [assignedTo:foreignKey]
  - STATUS: [status:ENUM]
    - ASSIGNED
    - PENDING
    - COMPLETED 
  - CREATED_AT: [createdAt:datetime]
  - UPDATED_AT: [updatedAt:datetime]
  - IS_ACTIVE: [isActive:boolean] 
 - PROJECT
  - ID: [id] .....
  - NAME: [name]
  - DESCRIPTION: [description]
  - OWNER_ID: [ownerId:foreignKey]
  - CREATED_AT: [createdAt:datetime]
  - UPDATED_AT: [updatedAt:datetime]
  - IS_ACTIVE: [isActive:boolean] 
- AUDIT
  - ID: [id] .....
  - ACTOR: [actor:foreignKey]
  - ACTION: [action:general_activity]
  - DETAIL: [detail:sub_activity]
  - CREATED_AT: [createdAt:datetime]
  - UPDATED_AT: [updatedAt:datetime]

RELATIONS:
- PROJECTS [MANY-ONE] MANAGER 
- TASK [MANY-ONE] MANAGER
- TASK [MANY-ONE] PROJECTS
- TASK [MANY-ONE] USER

API GROUPS:
- USER [roles => user, manager, admin] [PROTECT] [/users]
   - CREATE [POST] [/users]
      - ADMIN 
   - UPDATE [PUT/PATCH] [/users/<id>]
      - ADMIN
      - OWN USER
   - DELETE [DELETE] [/users/<id>]
      - ADMIN
      - OWN USER
   - READ  [GET] [/users/<id>]
      - ADMIN
      - OWN USER

- PROJECT  [/project]
   - CREATE [POST] 
      - ADMIN [ FOR ALL]
      - MANAGER  [ OWN PROJECTS]
   - UPDATE [PUT/PATCH]
      - ADMIN [ FOR ALL]
      - MANAGER  [ OWN PROJECTS]
   - DELETE [DELETE]
      - ADMIN [ FOR ALL]
      - MANAGER  [ OWN PROJECTS]  
   - READ [GET]
      - ADMIN [ALL]
      - MANAGER  [ALL]
      - USER [ALL]
- etc ..... [tasks, audits]

- BACKGROUND TASKS
  - Audit background tasks
 
- SCHEMAS [RESPONSE AND REQUEST]
  
   Common primitives (used by all endpoints)
    - ResponseEnvelope<T>
       - status: "success" | "error"
       - message: string
       - data: T | null
    - PageMeta
       - total: number
       - limit: number
       - offset: number
    - Page<T>
       - items: T[]
       - meta: PageMeta

   Conventions
    - Public JSON fields use camelCase for certain identifiers (e.g., ownerId, projectId, assignedTo, actorId).
    - Internal models use snake_case with Pydantic aliases (validation_alias / serialization_alias) to map to/from the public JSON.
    - Request models ignore unknown/extra fields.

   - USER [/users]
       - POST REQUEST [/users]: [UserPostRequest]
          - username: string
          - email: email
          - password: string
          - roles?: Role[] where Role ∈ { USER, MANAGER, ADMIN }
       - POST RESPONSE [/users]: [UserPostResponse]
          - envelope: ResponseEnvelope<UserRead>
          - UserRead
             - id: string
             - username: string
             - email: email
             - roles: Role[]
       - LIST RESPONSE [GET /users]
          - envelope: ResponseEnvelope<Page<UserRead>>

   - PROJECT [/project]
       - POST REQUEST [/project]: [ProjectPostRequest]
          - name: string
          - description?: string
          - ownerId: string
       - POST RESPONSE [/project]: [ProjectPostResponse]
          - envelope: ResponseEnvelope<ProjectRead>
          - ProjectRead
             - id: string
             - name: string
             - description?: string
             - ownerId: string
       - LIST RESPONSE [GET /project]
          - envelope: ResponseEnvelope<Page<ProjectRead>>

   - TASKS [/tasks]
       - POST REQUEST [/tasks]: [TaskPostRequest]
          - description: string
          - projectId: string
          - assignedTo?: string
          - status?: TaskStatus where TaskStatus ∈ { ASSIGNED, PENDING, COMPLETED }
       - POST RESPONSE [/tasks]: [TaskPostResponse]
          - envelope: ResponseEnvelope<TaskRead>
          - TaskRead
             - id: string
             - description: string
             - projectId: string
             - assignedTo?: string
             - status: TaskStatus
       - LIST RESPONSE [GET /tasks]
          - envelope: ResponseEnvelope<Page<TaskRead>>

   - AUDIT [/audits]
       - POST REQUEST [/audits]: [AuditPostRequest]
          - actorId: string
          - action: string
          - detail: string
       - POST RESPONSE [/audits]: [AuditPostResponse]
          - envelope: ResponseEnvelope<AuditRead>
          - AuditRead
             - id: string
             - actorId: string
             - action: string
             - detail: string
       - LIST RESPONSE [GET /audits]
          - envelope: ResponseEnvelope<Page<AuditRead>>

- REPOSITORIES:
   - USERS [CLASS]
     -
     -  
   - PROJECTS [CLASS]
     -
     -  
   - TASKS [CLASS]
     -
     -  
   - AUDIT [CLASS]
     -
     -  

 - SERVICES:
    - ORM SERVICE [super class]
       - Path: `app/services/orm_service.py`
       - Purpose: Thin layer over repositories providing consistent CRUD and pagination
       - Methods: `create`, `get`, `list`, `update`, `delete`
    - USER SERVICE [sub class]
       - Path: `app/services/user_service.py`
       - Purpose: User-specific operations on top of repository
       - Methods: `create_user` (hashes password), `get_user`, `list_users`, `update_user`, `delete_user`, `get_by_email`
    - PROJECT SERVICE [sub class]
       - Path: `app/services/project_service.py`
       - Purpose: Project operations
       - Methods: `get_project`, `list_projects` (+ base CRUD)
    - TASK SERVICE [sub class]
       - Path: `app/services/task_service.py`
       - Purpose: Task operations
       - Methods: `get_task`, `list_tasks` (+ base CRUD)
    - AUDIT SERVICE [sub class]
       - Path: `app/services/audit_service.py`
       - Purpose: Audit operations
       - Methods: `get_audit`, `list_audits` (+ base CRUD)
    - AUTHENTICATION SERVICE
       - Path: `app/services/authentication.py`
       - Purpose: Password hashing/verification and JWT token management
       - Methods: `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`
    - AUTHORIZATION SERVICE
       - Path: `app/services/authorization.py`
       - Purpose: RBAC helpers and ownership checks for route protection
       - Methods: `has_role`, `can_manage_user`
    - MODULE INDEX
       - Source: `app/services/__init__.py`
       - Exports: `ORMService`, `UserService`, `ProjectService`, `TaskService`, `AuditService`, `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`, `has_role`, `can_manage_user`
- TESTS:
  - INTEGRATION
  - UNIT TEST [ IN THE FEATURE] 
   ....coming soon..........

- Security
  - AUTHENTICATION
    - JWT [JSON WEB TOKEN]
  - AUTHORIZATION   
    - RBAC [ROLE BASED ACCESS CONTROL] 
  - CACHE
    - REDIS SESSION STORE

- ENVIRONMENT
  - APP VARIABLES 
   - # Application settings
      APP_NAME=Books Catalog API
      APP_VERSION=0.1.0
      APP_DESCRIPTION=A simple FastAPI application
      APP_DEBUG=True
      APP_HOST=127.0.0.1
      APP_PORT=8000
      APP_RELOAD=True
      APP_API_DOCS_URL=/docs
      APP_REDOC_URL=/redoc
      APP_SCALARA_URL=/scalar
      APP_OPENAPI_URL=/openapi.json

   - # Security settings
      SECURITY_SECRET_KEY=your_super_secret_key_here
      SECURITY_JWT_ALGORITHM=HS256
      SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES=30

   - # database settings
      DATABASE_HOST=localhost
      DATABASE_PORT=27019
      DATABASE_NAME=mydb
      DATABASE_USER=root
      DATABASE_PASSWORD=example
      DATABASE_AUTH_SOURCE=admin

   - # logger settings
      LOG_LEVEL=debug
      LOG_FORMAT=text #json #csv
      LOG_FILE=/var/log/app.log
      LOG_RETENTION=7d
      LOG_ROTATION=1d
      LOG_HANDLERS=console,file
      LOG_DATE_FORMAT=%Y-%m-%d %H:%M:%S
      LOG_HANDLERS=console,file
      
   - # Redis settings
      REDIS_HOST=localhost
      REDIS_PORT=6379
      REDIS_PASSWORD=???
      REDIS_DB=0
      REDIS_USERNAME=???
      REDIS_SSL=False
      REDIS_SSL_CERT_REQS=none
      REDIS_SOCKET_CONNECT_TIMEOUT=5
      REDIS_SOCKET_TIMEOUT=5
      REDIS_CONNECTION_POOL_MAX_CONNECTIONS=50
      REDIS_DECODE_RESPONSES=True

  - PLATFORM [DOCKER]
  - ORCHESTRATION: DOCKER COMPOSE
  - CONTAINERS
      - Python [LINUX CONTAINER FOR APP RUNNING]
      - Mongodb [ DOCUMENT BASED DATABASE]
      - Redis [ON MEMORY DATABASE]

-  LIBRARIES:
```
   fastapi 
   uvicorn 
   bcrypt
   python-multipart
   pydantic
   pydantic-settings 
   requests
   motor 
   beanie 
   pyjwt
   python-jose[cryptography] 
   passlib[bcrypt] 
   pytest
   pre-commit
   ruff
   mypy
```

- SCAFFOLDING
```
todoApp
├─ .vscode/ 
│  ├─ extensions.json
│  ├─ launch.json  
│  └─ settings.json
├─ app/
│  │  ├─ __init__.py
│  ├─ core/
│  │  ├─ __init__.py
│  │  ├─ api.py   # routs            
│  │  ├─ config.py # configuration 
│  │  └─ db.py 
│  ├─ models/
│  │  ├─ __init__.py
│  │  ├─ user.py
│  │  ├─ project.py
│  │  └─ etc ...
│  ├─ schemas/
│  │  ├─ __init__.py
│  │  ├─ user.py
│  │  ├─ project.py
│  │  └─ etc ...
│  ├─ repositories/
│  │  ├─ __init__.py
│  │  └─ user_repo.py
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ orm_service.py
│  │  ├─ user_service.py
│  │  ├─ project_service.py
│  │  ├─ task_service.py
│  │  ├─ audit_service.py
│  │  ├─ authentication.py
│  │  └─ authorization.py
│  └─ dependencies/
│     ├─ __init__.py
│     └─ auth.py
│     └─ common.py
├─ tests/
│  └─ test_users.py
├─ main.py
├─ __init__.py
├─ .env.example
├─ .pre-commit-config.yaml
├─ .mypy.ini
├─ .python-version
├─ ruff.toml
├─ uv.lock
├─ plan.md
├─ .gitignore
├─ pyproject.toml
├─ docker-compose.yml
├─ pytest.ini
└─ README.md
```