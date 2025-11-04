CXX := g++
CXXFLAGS := -std=c++20 -O2 -Wall -Wextra -I src
LDFLAGS :=

SRC_DIR := src
BUILD_DIR := build
TARGET := $(BUILD_DIR)/benchmark_runner

SOURCES := \
	$(SRC_DIR)/benchmark_runner.cpp \
	$(SRC_DIR)/io/graph_loader.cpp \
	$(SRC_DIR)/io/graph_writer.cpp \
	$(SRC_DIR)/io/results_logger.cpp \
	$(SRC_DIR)/algorithms/genetic.cpp

OBJECTS := $(SOURCES:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)

.PHONY: all clean run-genetic

all: $(TARGET)

$(TARGET): $(OBJECTS)
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(OBJECTS) -o $@ $(LDFLAGS)

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c $< -o $@

run-genetic: $(TARGET)
	$(TARGET) --algorithm genetic \
	    --input scripts/datasets/dimacs/myciel6.col \
	    --output results/raw/myciel6_genetic.col \
	    --results results/results.csv \
	    --graph-name myciel6

clean:
	rm -rf $(BUILD_DIR)

