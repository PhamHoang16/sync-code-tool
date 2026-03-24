pipeline {
    agent {
        label 'slave-1 || slave-2 || worker-ubuntu'
    }

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

    stages {
        stage('Checkout Sync Tool') {
            steps {
                checkout scm 
            }
        }

        stage('Execute Sync') {
            steps {
                script {
                    if (!params.SRC_TOKEN || !params.DEST_TOKEN) {
                        error("You must provide both GitHub and Bitbucket tokens to run this sync job!")
                    }

                    // Set environment variables directly to avoid Groovy string interpolation warning
                    env.SYNC_SRC_USER = params.SRC_USER ?: ''
                    env.SYNC_SRC_TOKEN = params.SRC_TOKEN
                    env.SYNC_DEST_USER = params.DEST_USER ?: ''
                    env.SYNC_DEST_TOKEN = params.DEST_TOKEN

                    // Auto-detect Python command
                    def pythonCmd = isUnix() ? 'python3' : 'python'

                    // Construct the base command
                    def cmd = "${pythonCmd} src/github_to_bitbucket_sync.py " +
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

    post {
        always {
            cleanWs()
        }
        success {
            echo "✅ Source code synchronization successful!"
        }
        failure {
            echo "❌ Synchronization failed. Please check the logs."
        }
    }
}
