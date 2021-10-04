pipeline {
    agent {
        docker {
            image 'python:3.8'
            args '-u root:sudo --network host'
        }
    }

    stages {
        stage('Test') {
            steps {
                dir('./api'){
                    sh 'yes | pip install -r requirements.txt --user'
                    sh 'chmod +x ./tests.sh '
                    sh './tests.sh'
                }
            }
        }
    }
}