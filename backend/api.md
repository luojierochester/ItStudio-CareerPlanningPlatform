## localhost:8080/api

所有返回的json对象总有如下格式

```
{
    "code": int,
    "message": string,
    "data": T
}
```

接下来将省略`/api`并只给出`T`的类声明

当`"code"`不是`200`时，`"data"`必定为`null`

部分`/api/test`的返回值不遵循上述格式

## /v1/auth

### POST /login

Authorization: 无

key: username, password

data：

```
{
    "username": string,
    "role": string,
    "token": sting,
    "expire": time
}
```

### GET /logout

Authorization: Bearer $Token

key: 无

data：

```
null
```

### GET /ask-code?email=******&type=register

Authorization: 无

key: 无

data：

```
null
```

### GET /ask-code?email=******&type=reset

Authorization: 无

key: 无

data：

```
null
```

### POST /register

Authorization: 无

key: 无

data：email, code, username, password

```
null
```

### POST /reset

Authorization: 无

key: email, code, password

data：

```
null
```

### GET /relogin

Authorization: Bearer $Token

key: 无

data：

```
{
    "token": sting,
    "expire": time
}
```

## /test

### GET /hello

Authorization: Bearer $Token

key: 无

回复：

```
Hello Kotlin WebFlux!
```