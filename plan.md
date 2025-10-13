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
  
  - USER [/user]
     - POST REQUEST [/user]: [ UserPostRequest] .....
       - username
       - email 
       - password
       - etc
     - POST RESPONSE [/user]: [ UserPostResponse] .....
       -  message
       -  status
       -  etc
  - etc ...  

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
     -  USER [sub class]
     -  projects [sub class]
     - etc ...
     - 
- DEPENDENCIES:
  - AUTHENTICATION
  - AUTHORIZATION

- TESTS:
  - INTEGRATION
  - UNIT TEST [ IN THE FEATURE] 
   ....coming soon..........

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
│  │  └─ user_service.py
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