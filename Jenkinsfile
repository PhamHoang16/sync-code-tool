pipeline {
    agent any // Hoặc dùng docker agent chứa sẵn python3 và git

    parameters {
        string(name: 'SRC_URL', defaultValue: '', description: 'URL của GitHub Repository (HTTPS)')
        string(name: 'DEST_URL', defaultValue: '', description: 'URL của Bitbucket Repository (HTTPS)')
        booleanParam(name: 'SYNC_ALL', defaultValue: false, description: 'Đồng bộ toàn bộ Branches (1:1)?')
        string(name: 'SRC_BRANCHES', defaultValue: 'main', description: 'Các nhánh nguồn (Ví dụ: main dev). Bỏ qua nếu chọn SYNC_ALL.')
        string(name: 'DEST_BRANCHES', defaultValue: 'master', description: 'Các nhánh đích (Ví dụ: master stag). Bỏ qua nếu chọn SYNC_ALL.')
    }

    environment {
        // Thiết lập biến môi trường để thông báo cho script dùng method environment variables
        AUTH_METHOD = 'env'
        SYNC_SRC_USER = 'your-github-bot-name' 
        SYNC_DEST_USER = 'your-bitbucket-bot-name'
    }

    stages {
        stage('Checkout Sync Tool') {
            steps {
                // Bước này clone thư mục chứa file github_to_bitbucket_sync.py về workspace
                checkout scm 
            }
        }

        stage('Execute Sync') {
            steps {
                // Bọc trong withCredentials để Jenkins tự chèn token vào biến môi trường một cách an toàn
                withCredentials([
                    usernamePassword(
                        credentialsId: 'github-sync-token',
                        usernameVariable: 'SYNC_SRC_USER',
                        passwordVariable: 'SYNC_SRC_TOKEN'
                    ),
                    usernamePassword(
                        credentialsId: 'bitbucket-sync-pass', 
                        usernameVariable: 'SYNC_DEST_USER', 
                        passwordVariable: 'SYNC_DEST_TOKEN'
                    )
                ]) {
                    script {
                        // Khởi tạo lệnh chạy cơ bản
                        def cmd = "python3 github_to_bitbucket_sync.py " +
                                  "--src-url '${params.SRC_URL}' " +
                                  "--dest-url '${params.DEST_URL}' " +
                                  "--auth-method env"
                        
                        // Nối thêm parameter tùy theo mode người dùng chọn
                        if (params.SYNC_ALL) {
                            cmd += " --sync-all"
                        } else {
                            // Tránh lỗi nếu user để trống nhánh lúc chưa chọn SYNC_ALL
                            if (!params.SRC_BRANCHES || !params.DEST_BRANCHES) {
                                error("Vui lòng điền nhánh nguồn và nhánh đích (hoặc chọn thẻ Sync All)!")
                            }
                            cmd += " --src-branches ${params.SRC_BRANCHES} " +
                                   "--dest-branches ${params.DEST_BRANCHES}"
                        }

                        // Thực thi lệnh bash
                        sh "${cmd}"
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs() // Dọn dẹp workspace sau khi chạy xong để bảo mật
        }
        success {
            echo "✅ Đồng bộ mã nguồn thành công!"
            // Có thể thêm tính năng gửi tin nhắn Slack/Teams ở đây
        }
        failure {
            echo "❌ Đồng bộ thất bại. Vui lòng kiểm tra lại logs."
        }
    }
}
