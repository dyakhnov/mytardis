def label = "app-${UUID.randomUUID().toString()}"
podTemplate(
    label: label,
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
            ]
        ),
        containerTemplate(
            name: 'mysql',
            image: 'mysql:latest',
            alwaysPullImage: false,
            envVars: [
                envVar(key: 'MYSQL_ROOT_PASSWORD', value: 'mysql')
            ]
        ),
        containerTemplate(
            name: 'postgres',
            image: 'postgres:latest',
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
    node(label) {
        def DOCKER_HUB_ACCOUNT = 'dyakhnov'
        def DOCKER_IMAGE_NAME = 'mytardis'
        def K8S_DEPLOYMENT_NAMESPACE = 'mytardis'
        stage('Clone repository') {
            checkout scm
        }
        // def TAG = sh(returnStdout: true, script: 'git tag --contains | head -1').trim()
        def TAG = sh(returnStdout: true, script: 'git log -n 1 --pretty=format:"%h"').trim()
        stage('Build image') {
            container('docker') {
                sh("docker build -t ${DOCKER_HUB_ACCOUNT}/${DOCKER_IMAGE_NAME}:${TAG} .")
            }
        }
        stage('Test image') {
            container('docker') {
                ['test_settings', 'test_on_mysql_settings', 'test_on_postgresql_settings'].each { item ->
                    sh("docker run ${DOCKER_HUB_ACCOUNT}/${DOCKER_IMAGE_NAME}:${TAG} python test.py test --settings=${item}")
                }
            }
        }
        stage('Push image') {
            container('docker') {
                sh("docker push ${DOCKER_HUB_ACCOUNT}/${DOCKER_IMAGE_NAME}:${TAG}")
                sh("docker tag ${DOCKER_HUB_ACCOUNT}/${DOCKER_IMAGE_NAME}:${TAG} ${DOCKER_HUB_ACCOUNT}/${DOCKER_IMAGE_NAME}:latest")
                sh("docker push ${DOCKER_HUB_ACCOUNT}/${DOCKER_IMAGE_NAME}:latest")
            }
        }
        stage('Deploy image') {
            container('kubectl') {
                ['mytardis', 'celery-worker', 'celery-filter', 'celery-beat'].each { item ->
                    sh ("kubectl -n ${K8S_DEPLOYMENT_NAMESPACE} set image deployment/${item} ${item}=${DOCKER_HUB_ACCOUNT}/${DOCKER_IMAGE_NAME}:${TAG}")
                }
            }
        }
    }
}
