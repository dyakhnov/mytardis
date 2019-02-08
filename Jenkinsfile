def workerLabel = 'mytardis'
def dockerHubAccount = 'dyakhnov'
def dockerImageName = 'mytardis'
def dockerImageTag = ''
def dockerImageFullNameTag = ''
def dockerImageFullNameLatest = "${dockerHubAccount}/${dockerImageName}:latest"
def k8sDeploymentNamespace = 'mytardis'

podTemplate(
    label: workerLabel,
    serviceAccount: 'jenkins',
    automountServiceAccountToken: true,
    containers: [
        containerTemplate(
            name: 'docker',
            image: 'docker:18.06.1-ce-dind',
            ttyEnabled: true,
            command: 'cat',
            envVars: [
                containerEnvVar(key: 'DOCKER_CONFIG', value: '/tmp/docker')
            ],
            resourceRequestCpu: '500m',
            resourceRequestMemory: '500Mi'
        ),
        containerTemplate(
            name: 'mysql',
            image: 'mysql:5.7',
            alwaysPullImage: false,
            envVars: [
                envVar(key: 'MYSQL_ROOT_PASSWORD', value: 'mysql')
            ]
        ),
        containerTemplate(
            name: 'postgres',
            image: 'postgres:9.3',
            alwaysPullImage: false,
            envVars: [
                envVar(key: 'POSTGRES_PASSWORD', value: 'postgres')
            ]
        ),
        containerTemplate(
            name: 'kubectl',
            image: 'lachlanevenson/k8s-kubectl:v1.13.0',
            ttyEnabled: true,
            command: 'cat',
            envVars: [
                containerEnvVar(key: 'KUBECONFIG', value: '/tmp/kube/config')
            ]
        )
    ],
    volumes: [
        secretVolume(secretName: 'kube-config', mountPath: '/tmp/kube'),
        secretVolume(secretName: 'docker-config', mountPath: '/tmp/docker'),
        hostPathVolume(hostPath: '/var/run/docker.sock', mountPath: '/var/run/docker.sock')
    ]
) {
    node(workerLabel) {
        def ip = sh(returnStdout: true, script: 'hostname -i').trim()
        stage('Clone repository') {
            checkout scm
        }
        dockerImageTag = sh(returnStdout: true, script: 'git log -n 1 --pretty=format:"%h"').trim()
        dockerImageFullNameTag = "${dockerHubAccount}/${dockerImageName}:${dockerImageTag}"
        stage('Build test image') {
            container('docker') {
                sh("docker build . --tag ${dockerImageFullNameTag} --target=test")
            }
        }
        stage('Test image') {
            container('docker') {
                parallel (
                    //'pylint': {
                    //    sh("docker run ${dockerImageFullNameTag} pylint --rcfile .pylintrc tardis")
                    //},
                    'memory': {
                        sh("docker run ${dockerImageFullNameTag} python test.py test --settings=tardis.test_settings")
                    },
                    'mysql': {
                        sh("docker run --add-host mysql:${ip} ${dockerImageFullNameTag} python test.py test --settings=tardis.test_on_mysql_settings")
                    },
                    'postgres': {
                        sh("docker run --add-host postgres:${ip} ${dockerImageFullNameTag} python test.py test --settings=tardis.test_on_postgresql_settings")
                    }
                )
            }
        }
        stage('Build production image') {
            container('docker') {
                sh("docker build . --tag ${dockerImageFullNameTag} --target=base")
            }
        }
        stage('Push production image') {
            container('docker') {
                sh("docker push ${dockerImageFullNameTag}")
                sh("docker tag ${dockerImageFullNameTag} ${dockerImageFullNameLatest}")
                sh("docker push ${dockerImageFullNameLatest}")
            }
        }
        stage('Deploy production image') {
            container('kubectl') {
                ['mytardis', 'celery-worker', 'celery-filter', 'celery-beat'].each { item ->
                    sh ("kubectl -n ${k8sDeploymentNamespace} set image deployment/${item} ${item}=${dockerImageFullNameTag}")
                }
            }
        }
    }
}
