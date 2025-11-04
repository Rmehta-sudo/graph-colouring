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

GRAPH ?= dimacs/myciel6.col
GRAPH_PATH := scripts/datasets/$(GRAPH)
GRAPH_FILE := $(notdir $(GRAPH))
GRAPH_NAME := $(basename $(GRAPH_FILE))
OUTPUT ?= results/raw/$(GRAPH_NAME)_genetic.col
RESULTS ?= results/results.csv

all: $(TARGET)

$(TARGET): $(OBJECTS)
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(OBJECTS) -o $@ $(LDFLAGS)

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c $< -o $@

run-genetic: $(TARGET)
	$(TARGET) --algorithm genetic \
	    --input $(GRAPH_PATH) \
	    --output $(OUTPUT) \
	    --results $(RESULTS) \
	    --graph-name $(GRAPH_NAME)

clean:
	rm -rf $(BUILD_DIR)

