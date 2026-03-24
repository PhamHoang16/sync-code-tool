pipeline {
    agent any // Or use a docker agent with python3 and git pre-installed

    parameters {
        string(name: 'SRC_URL', defaultValue: '', description: 'GitHub Repository URL (HTTPS)')
        string(name: 'DEST_URL', defaultValue: '', description: 'Bitbucket Repository URL (HTTPS)')
        string(name: 'SRC_USER', defaultValue: '', description: '[Optional] GitHub Username (Can be left blank for PATs)')
        password(name: 'SRC_TOKEN', defaultValue: '', description: 'Input your GitHub Token (PAT)')
        string(name: 'DEST_USER', defaultValue: '', description: '[Optional] Bitbucket Username (Required if using App Passwords)')
        password(name: 'DEST_TOKEN', defaultValue: '', description: 'Input your Bitbucket Token (App Password / HTTP Token)')
        booleanParam(name: 'SYNC_ALL', defaultValue: false, description: 'Sync all branches (1:1 mapping)?')
        string(name: 'SRC_BRANCHES', defaultValue: 'main', description: 'Source branches (e.g., main dev). Ignored if SYNC_ALL is checked.')
        string(name: 'DEST_BRANCHES', defaultValue: 'master', description: 'Destination branches (e.g., master stag). Ignored if SYNC_ALL is checked.')
    }

    environment {
        // Enforce environment variable authentication mode
        AUTH_METHOD = 'env'
        SYNC_SRC_USER = "${params.SRC_USER}"
        SYNC_SRC_TOKEN = "${params.SRC_TOKEN}"
        SYNC_DEST_USER = "${params.DEST_USER}"
        SYNC_DEST_TOKEN = "${params.DEST_TOKEN}"
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
                script {
                    if (!params.SRC_TOKEN || !params.DEST_TOKEN) {
                        error("You must provide both GitHub and Bitbucket tokens to run this sync job!")
                    }

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
