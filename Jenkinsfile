pipeline {
    agent any // Or use a docker agent with python3 and git pre-installed

    parameters {
        string(name: 'SRC_URL', defaultValue: '', description: 'GitHub Repository URL (HTTPS)')
        string(name: 'DEST_URL', defaultValue: '', description: 'Bitbucket Repository URL (HTTPS)')
        credentials(name: 'GITHUB_CRED_ID', defaultValue: 'github-sync-token', description: 'Select GitHub Credential (Type: Username with password)', credentialType: 'com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl', required: true)
        credentials(name: 'BITBUCKET_CRED_ID', defaultValue: 'bitbucket-sync-pass', description: 'Select Bitbucket Credential (Type: Username with password)', credentialType: 'com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl', required: true)
        booleanParam(name: 'SYNC_ALL', defaultValue: false, description: 'Sync all branches (1:1 mapping)?')
        string(name: 'SRC_BRANCHES', defaultValue: 'main', description: 'Source branches (e.g., main dev). Ignored if SYNC_ALL is checked.')
        string(name: 'DEST_BRANCHES', defaultValue: 'master', description: 'Destination branches (e.g., master stag). Ignored if SYNC_ALL is checked.')
    }

    environment {
        // Enforce environment variable authentication mode
        AUTH_METHOD = 'env'
        SYNC_SRC_USER = 'your-github-bot-name' 
        SYNC_DEST_USER = 'your-bitbucket-bot-name'
    }

    stages {
        stage('Checkout Sync Tool') {
            steps {
                // Clone the repository containing github_to_bitbucket_sync.py
                checkout scm 
            }
        }

        stage('Execute Sync') {
            steps {
                // Wrap in withCredentials to securely inject tokens into environment variables
                withCredentials([
                    usernamePassword(
                        credentialsId: params.GITHUB_CRED_ID,
                        usernameVariable: 'SYNC_SRC_USER',
                        passwordVariable: 'SYNC_SRC_TOKEN'
                    ),
                    usernamePassword(
                        credentialsId: params.BITBUCKET_CRED_ID, 
                        usernameVariable: 'SYNC_DEST_USER', 
                        passwordVariable: 'SYNC_DEST_TOKEN'
                    )
                ]) {
                    script {
                        // Construct the base command
                        def cmd = "python3 src/github_to_bitbucket_sync.py " +
                                  "--src-url '${params.SRC_URL}' " +
                                  "--dest-url '${params.DEST_URL}' " +
                                  "--auth-method env"
                        
                        // Append parameters based on user selection
                        if (params.SYNC_ALL) {
                            cmd += " --sync-all"
                        } else {
                            // Prevent error if branches are empty and SYNC_ALL is not checked
                            if (!params.SRC_BRANCHES || !params.DEST_BRANCHES) {
                                error("Please provide source and destination branches (or check Sync All)!")
                            }
                            cmd += " --src-branches ${params.SRC_BRANCHES} " +
                                   "--dest-branches ${params.DEST_BRANCHES}"
                        }

                        // Execute the bash command
                        sh "${cmd}"
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs() // Clean up workspace after execution for security
        }
        success {
            echo "✅ Source code synchronization successful!"
            // Can add Slack/Teams notification here
        }
        failure {
            echo "❌ Synchronization failed. Please check the logs."
        }
    }
}
