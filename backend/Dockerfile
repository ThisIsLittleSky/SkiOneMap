FROM eclipse-temurin:17-jdk AS build
WORKDIR /app

RUN sed -i 's|http://archive.ubuntu.com|http://mirrors.aliyun.com|g' /etc/apt/sources.list /etc/apt/sources.list.d/*.list 2>/dev/null; \
    sed -i 's|http://security.ubuntu.com|http://mirrors.aliyun.com|g' /etc/apt/sources.list /etc/apt/sources.list.d/*.list 2>/dev/null; \
    apt-get update && apt-get install -y maven && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /root/.m2 && \
    echo '<?xml version="1.0" encoding="UTF-8"?><settings><mirrors><mirror><id>aliyun</id><mirrorOf>central</mirrorOf><name>aliyun</name><url>https://maven.aliyun.com/repository/public</url></mirror></mirrors></settings>' > /root/.m2/settings.xml

COPY pom.xml .
RUN mvn dependency:resolve -B

COPY src ./src
RUN mvn package -DskipTests -B

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
RUN mkdir -p /data/videos
EXPOSE 8085
ENTRYPOINT ["java", "-jar", "app.jar"]
