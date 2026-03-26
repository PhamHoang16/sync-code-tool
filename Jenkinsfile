pipeline {
    agent { label "worker-linux" }

    options {
        disableConcurrentBuilds()
    }

    parameters {
        string(name: 'SRC_URL', defaultValue: '', description: 'Source Repository URL (HTTPS or SSH)')
        string(name: 'DEST_URL', defaultValue: '', description: 'Destination Repository URL (HTTPS or SSH)')
        
        string(name: 'SRC_USER', defaultValue: '', description: 'Source Username (Optional for some PATs)')
        password(name: 'SRC_TOKEN', defaultValue: '', description: 'Source Access Token or Password')
        
        credentials(name: 'DEST_CRED_ID', defaultValue: '', description: 'Select Destination credential (Type: Username with password)', credentialType: 'com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl', required: true)
        
        booleanParam(name: 'SYNC_ALL', defaultValue: true, description: 'Sync all branches (1:1 mapping)?')
        string(name: 'IGNORE_BRANCHES', defaultValue: 'release main master uat production prod', description: 'Space-separated list of branches to ignore in Sync All mode (e.g., master production)')
        
        string(name: 'SRC_BRANCHES', defaultValue: '', description: 'Source branches to sync. Space-separated (e.g., main dev feature/xyz). Ignored if Sync All is checked.')
        string(name: 'DEST_BRANCHES', defaultValue: '', description: 'Destination branches mapping. Space-separated (e.g., master stag feature/xyz). Ignored if Sync All is checked.')
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
                        credentialsId: params.DEST_CRED_ID,
                        usernameVariable: 'SYNC_DEST_USER',
                        passwordVariable: 'SYNC_DEST_TOKEN'
                    )
                ]) {
                    withEnv([
                        "SYNC_SRC_USER=${params.SRC_USER ?: ''}",
                        "SYNC_SRC_TOKEN=${params.SRC_TOKEN}"
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
                                if (params.IGNORE_BRANCHES?.trim()) {
                                    cmd += " --ignore-branches ${params.IGNORE_BRANCHES}"
                                }
                            } else {
                                if (!params.SRC_BRANCHES?.trim() || !params.DEST_BRANCHES?.trim()) {
                                    error("Please provide source and destination branches (or check Sync All)!")
                                }
                                cmd += " --src-branches ${params.SRC_BRANCHES} --dest-branches ${params.DEST_BRANCHES}"
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
