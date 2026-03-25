pipeline {
    agent { label "worker-linux" }

    options {
        disableConcurrentBuilds()
    }

    parameters {
        string(name: 'SRC_URL', defaultValue: '', description: 'Source Repository URL (HTTPS)')
        string(name: 'DEST_URL', defaultValue: '', description: 'Destination Repository URL (HTTPS)')
        credentials(name: 'SRC_CRED_ID', defaultValue: '', description: 'Select Source credential (Type: Username with password)', credentialType: 'com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl', required: true)
        credentials(name: 'DEST_CRED_ID', defaultValue: '', description: 'Select Destination credential (Type: Username with password)', credentialType: 'com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl', required: true)
        booleanParam(name: 'SYNC_ALL', defaultValue: false, description: 'Sync all branches (1:1 mapping)?')
        string(name: 'SRC_BRANCHES', defaultValue: 'main', description: 'Source branches (e.g., main dev). Ignored if SYNC_ALL is checked.')
        string(name: 'DEST_BRANCHES', defaultValue: 'master', description: 'Destination branches (e.g., master stag). Ignored if SYNC_ALL is checked.')
    }

    stages {
        stage('Checkout Sync Tool') {
            steps {
                retry(3) {
                    checkout scm
                }
            }
        }

        stage('Execute Sync') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: params.SRC_CRED_ID,
                        usernameVariable: 'SYNC_SRC_USER',
                        passwordVariable: 'SYNC_SRC_TOKEN'
                    ),
                    usernamePassword(
                        credentialsId: params.DEST_CRED_ID,
                        usernameVariable: 'SYNC_DEST_USER',
                        passwordVariable: 'SYNC_DEST_TOKEN'
                    )
                ]) {
                    script {
                        // Input validation
                        if (!params.SRC_URL?.trim() || !params.DEST_URL?.trim()) {
                            error("Both Source URL and Destination URL are required!")
                        }

                        // Auto-detect Python command
                        def pythonCmd = isUnix() ? 'python3' : 'python'

                        // Construct the base command
                        def cmd = "${pythonCmd} src/git_repo_sync.py " +
                                  "--src-url \"${params.SRC_URL}\" " +
                                  "--dest-url \"${params.DEST_URL}\" " +
                                  "--auth-method env"

                        if (params.SYNC_ALL) {
                            cmd += " --sync-all"
                        } else {
                            if (!params.SRC_BRANCHES || !params.DEST_BRANCHES) {
                                error("Please provide source and destination branches (or check Sync All)!")
                            }
                            cmd += " --src-branches ${params.SRC_BRANCHES} " +
                                   "--dest-branches ${params.DEST_BRANCHES}"
                        }

                        if (isUnix()) {
                            sh "${cmd}"
                        } else {
                            bat "${cmd}"
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo "✅ Repository synchronization successful!"
        }
        failure {
            echo "❌ Synchronization failed. Please check the logs."
        }
    }
}
