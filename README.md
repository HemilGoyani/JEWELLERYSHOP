# Reports Admin

## Setup the project

Clone the project using Git.

```sh
git clone git@github.com:HemilGoyani/JEWELLERYSHOP.git
cd TSS
```

### Create .env file

```sh
cp .env.sample .env
```

### Run the docker containers

```sh
docker-compose up -d --build
```

### Migrate the database

```sh
docker-compose exec django python manage.py migrate
```

### Create the super user

```sh
docker-compose exec django python manage.py createsuperuser
```

The project is now running on http://127.0.0.1:8000.
