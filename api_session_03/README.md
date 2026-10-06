1. Xác định resources
user, profile, post, comment, tag, và quan hệ follow (user theo dõi user)
2. Phân loại
Collection: /users, /posts, /tags
Item: /users/{id}, /posts/{id}, /tags/{id}
Sub-resource: /posts/{id}/comments, /posts/{id}/tags, /users/{id}/posts, /users/{id}/followers, /users/{id}/following
3. Sơ đồ cây endpoint
/api
└── /v1                                        ← version segment
    │
    ├── /posts                               
    │   │     GET   
    │   │     POST  
    │   │
    │   └── /{post_id}                       
    │       │     GET
    │       │     PUT     
    │       │     PATCH   
    │       │     DELETE  
    │       │
    │       └── /comments                     
    │           │     GET, POST
    │           │
    │           └── /{comment_id}              
    │                 GET, PATCH, DELETE
    │
    └── /authors                              
        │     GET, POST
        │
        └── /{author_id}                       
            │     GET, PUT, PATCH, DELETE
            │
            └── /posts                         
    