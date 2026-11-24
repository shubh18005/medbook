# Optional: used only when hosting the backend on a service such as Render/Railway.
# NOTE: written for deployment but not tested by the authors.
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 4001
ENTRYPOINT ["java","-jar","app.jar"]
