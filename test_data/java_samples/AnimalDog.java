package com.example.zoo;

public class Dog extends Animal {
    private String breed;

    public Dog(String breed) {
        this.breed = breed;
    }

    public String bark() {
        return "Woof!";
    }
}
