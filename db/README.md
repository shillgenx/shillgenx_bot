### MacOS
* Download MongoDB
    * ```brew tap mongodb/brew```
    * ```brew install mongodb-community```
* Start MongoDB
    * ```brew services start mongodb/brew/mongodb-community```
* Access MongoDB shell
    * ```mongosh```
* Stop MongoDB
    * ```brew services stop mongodb/brew/mongodb-community```

### Linux
* Import the MongoDB Public GPG Key
    * ```wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -```
* Create a list file for MongoDB
    * ```echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list```
* Install MongoDB
    * ```sudo apt-get update```
    * ```sudo apt-get install -y mongodb-org```
* Start MongoDB service
    ```sudo systemctl start mongod```
* Check if MongoDB is running
    * ```sudo systemctl status mongod```
* Enable MongoDB to start on boot (optional)
    * ```sudo systemctl enable mongod```
* Access MongoDB shell
    * ```mongosh```
* Configure MongoDB (Recommended)
    * Edit MongoDB configuration file
        * Open ```/etc/mongod.conf``` in a text editor (vim)
        * Make necessary changes like binding to a different IP or changing the data directory.
        * Save the file and exit.
    * Restart MongoDB
        * Save the file and exit.
* Setup Authentication (Recommended)
    * Access MongoDB shell
        * ```mongosh```
    * Create an admin user
        * use admin
        * ```
        db.createUser({
            user: "yourAdminUser",
            pwd: "yourAdminPass",
                roles: [{ role: "userAdminAnyDatabase", db: "admin" }]
        })
        ```
    * Enable authentication
        * Edit ```/etc/mongod.conf```
        * Under the security section, add authorization: enabled.
        * Restart MongoDB
    * Test authentication
        * ```mongosh -u yourAdminUser -p yourAdminPass --authenticationDatabase admin```


### Create Non-Admin Authenticated User
* Login as Admin
    * ```mongosh -u yourAdminUser -p yourAdminPass --authenticationDatabase admin```
* Create the new user with rw access
    * ```use test_database```
    * ```
    db.createUser({
        user: "test_username",
        pwd: "test_password",
        roles: [{ role: "readWrite", db: "test_database" }]
    })
    ```
* Test the new user
    * mongosh -u test_username -p test_password --authenticationDatabase test_database
    