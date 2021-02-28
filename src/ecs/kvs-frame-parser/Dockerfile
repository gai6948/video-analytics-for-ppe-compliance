FROM maven:3.6-amazoncorretto-11 AS builder
# ----
# Install project dependencies and keep sources
# make source folder
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
# install maven dependency packages (keep in image)
COPY pom.xml /usr/src/app
RUN mvn -T 40 install -am && rm -rf target
# copy other source files (keep in image)
COPY src /usr/src/app/src
RUN mvn package
RUN ls target

# Copy build artifacts to runtime container
FROM openjdk:8-jdk-alpine
RUN mkdir -p /usr/app
WORKDIR /usr/app
COPY --from=builder /usr/src/app/target/kvsframeparser-1.0-SNAPSHOT-jar-with-dependencies.jar kvsframeparser-1.0-SNAPSHOT-jar-with-dependencies.jar

# Run the fat jar executable
ENTRYPOINT ["java", "-jar", "/usr/app/kvsframeparser-1.0-SNAPSHOT-jar-with-dependencies.jar"]